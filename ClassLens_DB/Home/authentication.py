# # Home/authentication.py

# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
# from .models import AdminUser

# class CustomAdminAuthentication(JWTAuthentication):
#     def get_user(self, validated_token):
#         print("--- Custom Auth is Running ---") # Debug Print
        
#         try:
#             # 1. Check if user_id is in the token
#             user_id = validated_token.get('user_id')
#             print(f"Token User ID: {user_id}") # Debug Print
            
#             if not user_id:
#                 raise InvalidToken('Token is missing user_id')

#             # 2. Try to find the user in YOUR custom table
#             user = AdminUser.objects.get(id=user_id)
#             print(f"Found User: {user.username}") # Debug Print
#             return user
            
#         except AdminUser.DoesNotExist:
#             print("User does not exist in AdminUser table") # Debug Print
#             raise AuthenticationFailed('User not found', code='user_not_found')
#         except Exception as e:
#             print(f"Auth Error: {str(e)}") # Debug Print
#             raise InvalidToken('Token validation error')



# Home/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import AdminUser

class CustomAdminAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        print("--- Custom Auth is Running ---")
        print(f"Full token payload: {validated_token}")
        
        try:
            user_id = validated_token.get('user_id')
            print(f"Token User ID: {user_id}")
            
            if not user_id:
                print("No user_id in token")
                raise InvalidToken('Token is missing user_id')

            user = AdminUser.objects.get(id=user_id)
            print(f"Found User: {user.username}")
            return user
            
        except AdminUser.DoesNotExist:
            print(f"User with id {user_id} does not exist in AdminUser table")
            raise AuthenticationFailed('User not found', code='user_not_found')
        except Exception as e:
            print(f"Auth Error: {str(e)}")
            raise InvalidToken('Token validation error')