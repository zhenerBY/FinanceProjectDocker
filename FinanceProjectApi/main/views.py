from datetime import date, datetime, timedelta

from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from concurrent.futures import as_completed
import time

from django.db.models import Q, Sum
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_api_key.permissions import HasAPIKey

from main.models import Category, AdvUser, Operation, ApiUser
from main.serializers import UsersSerializer, OperationsSerializer, CategoriesSerializer, ApiUsersSerializer, \
    ExtendedOperationsSerializer


class UsersViewSet(viewsets.ModelViewSet):
    queryset = AdvUser.objects.all()
    serializer_class = UsersSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAuthenticatedOrReadOnly]
        elif self.action == 'create':
            permission_classes = [IsAuthenticatedOrReadOnly]
        elif self.action == 'register':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(id=self.request.user.id)
        return queryset

    @action(methods=['POST'], detail=False, url_path="register")
    def register(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        u = AdvUser(username=username)
        u.set_password(password)
        if first_name is not None:
            u.first_name = first_name
        if last_name is not None:
            u.last_name = last_name
        if email is not None:
            u.email = email
        u.save()
        refresh = RefreshToken.for_user(u)
        res_data = {
            "user": UsersSerializer(u).data,
            "token": {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }
        return Response(res_data, status=status.HTTP_201_CREATED)


class OperationsViewSet(viewsets.ModelViewSet):
    queryset = Operation.objects.all()
    serializer_class = OperationsSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True)
        if self.request.method in ('GET', 'DELETE', 'PUT', 'PATH'):
            if self.request.data != {}:
                q = Q()
                if 'chat_id' in self.request.data.keys():
                    q &= Q(user__chat_id=self.request.data['chat_id'])
                if 'cat_type' in self.request.data.keys():
                    q &= Q(category__cat_type=self.request.data['cat_type'])
                if 'category' in self.request.data.keys():
                    q &= Q(category=self.request.data['category'])
                if 'date_filter_start' in self.request.data.keys():
                    date_filter_start = date.fromisoformat(self.request.data['date_filter_start'])
                    q &= Q(created_at__date__gt=date_filter_start)
                    if 'date_filter_end' in self.request.data.keys():
                        date_filter_end = date.fromisoformat(self.request.data['date_filter_end'])
                    else:
                        date_filter_end = datetime.now().date()
                    q &= Q(created_at__date__lt=date_filter_end)
                queryset = queryset.filter(q)
        return queryset

    # отлавливаем и переопледеляем request.data, если есть в запросе 'chat_id'
    def get_serializer(self, *args, **kwargs):
        if self.request.data.get("chat_id") is not None:
            user = ApiUser.objects.get(chat_id=self.request.data['chat_id']).pk
            self.request.data['user'] = user
        return super().get_serializer(*args, **kwargs)

    # shows income and expenses (2 numbers)
    @action(methods=['GET'], detail=False, url_path="balance")
    def balance(self, request):
        q = Q(is_active=True)
        if 'chat_id' in self.request.data.keys():
            q &= Q(user__chat_id=self.request.data['chat_id'])
        if 'date_filter_start' in self.request.data.keys():
            date_filter_start = date.fromisoformat(self.request.data['date_filter_start'])
            q &= Q(created_at__date__gt=date_filter_start)
            if 'date_filter_end' in self.request.data.keys():
                date_filter_end = date.fromisoformat(self.request.data['date_filter_end'])
            else:
                date_filter_end = datetime.now().date()
            q &= Q(created_at__date__lt=date_filter_end)
        q_inc = q & Q(category__cat_type='INC')
        q_exp = q & Q(category__cat_type='EXP')
        # start = time.time()
        # not threading start
        # inc = Operation.objects.aggregate(inc=Sum('amount', filter=q_inc))
        # exp = Operation.objects.aggregate(exp=Sum('amount', filter=q_exp))
        # not threading finish
        # threading start
        with PoolExecutor(max_workers=8) as executor:
            arguments = [
                {'inc': Sum('amount', filter=q_inc)},
                {'exp': Sum('amount', filter=q_exp)},
            ]
            req_pool = {executor.submit(Operation.objects.aggregate, **params): params for params in arguments}
            for req in as_completed(req_pool):
                params = req_pool[req]
                try:
                    data = req.result()
                except Exception as exc:
                    print(f'{params} exception: {exc}')
                else:
                    if 'exp' in data.keys():
                        exp = data
                    elif 'inc' in data.keys():
                        inc = data
        # threading finish
        # stop = time.time()
        # print(stop - start)
        res_data = {
            "balance": {
                **inc,
                **exp,
            }
        }
        return Response(res_data, status=status.HTTP_200_OK)

    # show user's category balance
    @action(methods=['GET'], detail=False, url_path="cat_balance")
    def cat_balance(self, request):
        cat_type = request.data.get('cat_type')
        q = Q(is_active=True) & Q(category__cat_type=cat_type)
        if 'chat_id' in self.request.data.keys():
            q &= Q(user__chat_id=self.request.data['chat_id'])
        if 'date_filter_start' in self.request.data.keys():
            date_filter_start = date.fromisoformat(self.request.data['date_filter_start'])
            q &= Q(created_at__date__gt=date_filter_start)
            if 'date_filter_end' in self.request.data.keys():
                date_filter_end = date.fromisoformat(self.request.data['date_filter_end'])
            else:
                date_filter_end = datetime.now().date()
            q &= Q(created_at__date__lt=date_filter_end)
        categories = {}
        for operation in Operation.objects.filter(q):
            if operation.category.name in categories.keys():
                categories[operation.category.name] += operation.amount
            else:
                categories[operation.category.name] = operation.amount
        res_data = {
            "categories": categories
        }
        return Response(res_data, status=status.HTTP_200_OK)


class ExtendedOperationsViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Operation.objects.all()
    serializer_class = ExtendedOperationsSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True)
        if self.request.method in ('GET',):
            try:
                queryset = queryset.filter(user__chat_id=self.request.data['chat_id'])
            except KeyError:
                queryset = queryset
        return queryset

    # отлавливаем и переопледеляем request.data, если есть в запросе 'chat_id'
    def get_serializer(self, *args, **kwargs):
        if self.request.data.get("chat_id") is not None:
            user = ApiUser.objects.get(chat_id=self.request.data['chat_id']).pk
            self.request.data['user'] = user
        return super().get_serializer(*args, **kwargs)


class CategoriesViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoriesSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        q = Q()
        if self.request.method in ('GET',):
            if 'cat_type' in self.request.data.keys():
                q &= Q(cat_type=self.request.data['cat_type'])
            if 'chat_id' in self.request.data.keys():
                q &= Q(user__chat_id=self.request.data['chat_id'])
            if 'unused' in self.request.data.keys():
                if self.request.data['unused'] is True:
                    queryset = queryset.filter(q).distinct()
                    q = Q(operations__is_active=True)
                    q &= Q(operations__user__chat_id=self.request.data['chat_id'])
                    queryset = queryset.exclude(q).distinct()
                else:
                    q &= Q(operations__is_active=True)
                    q &= Q(operations__user__chat_id=self.request.data['chat_id'])
                    queryset = queryset.filter(q).distinct()
            else:
                queryset = queryset.filter(q).distinct()
        return queryset

    def get_serializer(self, *args, **kwargs):
        if self.request.data.get("chat_id") is not None:
            user = ApiUser.objects.get(chat_id=self.request.data['chat_id']).pk
            self.request.data['user'] = user
        return super().get_serializer(*args, **kwargs)


class ApiUsersViewSet(viewsets.ModelViewSet):
    queryset = ApiUser.objects.all()
    serializer_class = ApiUsersSerializer
    permission_classes = [HasAPIKey]

    def get_permissions(self):
        if self.action == 'apikey':
            permission_classes = [AllowAny]
        else:
            permission_classes = [HasAPIKey]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method in ('GET', 'DELETE', 'PUT', 'PATH'):
            try:
                queryset = queryset.filter(chat_id=self.request.data['chat_id'])
            except KeyError:
                queryset = queryset
        return queryset

    # return APIKEY (used only 4 docker-compose)
    @action(methods=['GET'], detail=False, url_path="apikey")
    def apikey(self, request):
        with open('./key', 'r') as f:
            apikey = f.read()
        res_data = {
            "apikey": apikey
        }
        with open('./key', 'w') as f:
            f.write('None')
        return Response(res_data, status=status.HTTP_200_OK)
