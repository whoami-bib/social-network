from rest_framework import status,generics,filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer, LoginSerializer,UserSerializer,FriendRequestSerializer
from .models import User,FriendRequest
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils.timezone import now
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone


class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)

            return Response({
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# views for search functionality and pagination
class UserSearchView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [IsAuthenticated]  # Only authenticated users can access
    pagination_class = None  # We will enable pagination in the function

    def get_queryset(self):
        query = self.request.query_params.get('search', '')  # Get the search keyword
        if query:
            # Search for exact email or name containing the search keyword
            return User.objects.filter(
                Q(email__iexact=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
        return User.objects.none()  # Return empty queryset if no search keyword

    def paginate_queryset(self, queryset):
        paginator = self.paginator
        if paginator is None:
            return None
        return paginator.paginate_queryset(queryset, self.request)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginated_queryset = self.paginate_queryset(queryset)
        if paginated_queryset is not None:
            return self.get_paginated_response(self.get_serializer(paginated_queryset, many=True).data)
        return Response(self.get_serializer(queryset, many=True).data)
    
# views for handling friend requests

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_friend_request(request):
    if FriendRequest.objects.filter(sender=request.user, created_at__gte=now()-timezone.timedelta(minutes=1)).count() >= 3:
        return Response({'detail': 'You cannot send more than 3 friend requests per minute.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    receiver_id = request.data.get('receiver')
    print(receiver_id)
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.user == receiver:
        return Response({'detail': 'You cannot send a friend request to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

    if FriendRequest.objects.filter(sender=request.user, receiver=receiver).exists():
        return Response({'detail': 'Friend request already sent.'}, status=status.HTTP_400_BAD_REQUEST)

    friend_request = FriendRequest.objects.create(sender=request.user, receiver=receiver)
    serializer = FriendRequestSerializer(friend_request)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def accept_friend_request(request, pk):
    try:
        friend_request = FriendRequest.objects.get(pk=pk, receiver=request.user)
    except FriendRequest.DoesNotExist:
        return Response({'detail': 'Friend request not found.'}, status=status.HTTP_404_NOT_FOUND)

    friend_request.delete()
    return Response({'detail': 'Friend request accepted.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_friend_request(request, pk):
    try:
        friend_request = FriendRequest.objects.get(pk=pk, receiver=request.user)
    except FriendRequest.DoesNotExist:
        return Response({'detail': 'Friend request not found.'}, status=status.HTTP_404_NOT_FOUND)

    friend_request.delete()
    return Response({'detail': 'Friend request rejected.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_friends(request):
    friends = User.objects.filter(Q(sent_requests__receiver=request.user) | Q(received_requests__sender=request.user))
    serializer = UserSerializer(friends, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_pending_friend_requests(request):
    pending_requests = FriendRequest.objects.filter(receiver=request.user)
    serializer = FriendRequestSerializer(pending_requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)