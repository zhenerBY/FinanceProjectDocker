from django.urls import path, include

from rest_framework.routers import SimpleRouter

from main.views import UsersViewSet, OperationsViewSet, CategoriesViewSet, ApiUsersViewSet, ExtendedOperationsViewSet

router = SimpleRouter()
router.register('users', UsersViewSet, basename='users')
router.register('apiusers', ApiUsersViewSet, basename='apiusers')
router.register('operations', OperationsViewSet, basename='operations')
router.register('ext_operations', ExtendedOperationsViewSet, basename='ext_operations')
router.register('categories', CategoriesViewSet, basename='categories')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
