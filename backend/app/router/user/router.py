from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm.exc import NoResultFound
from uuid import UUID
from sqlmodel import Session

from app.database.config import get_db_session
from app.database.user.service import UserService
from app.database.user.model import UserCreate, UserModel, UserUpdate
from app.util.auth import AuthUtil
from .dependency import get_current_user
from app.config import constants

router = APIRouter(prefix="/user", tags=["Users"])

@router.get("/")
async def get_users(db_session=Depends(get_db_session)):
    """
    Endpoint to retrieve a list of users.

    This function uses a dependency to get a database session and then
    calls the UserService to fetch all users from the database. It 
    returns the list of users if available, otherwise an empty list.

    Args:
    db_session: Database session dependency, provided by the get_db_session function.

    Returns:
    A list of user objects or an empty list if no users are found.
    """ 
    user_service = UserService(db_session=db_session)
    result = await user_service.get_users()
    if not result:
        return []
    return result

@router.post("/", response_model=UserModel)
async def add_user(
    user: UserCreate,
    db_session = Depends(get_db_session)
):
    """
    Endpoint to add a new user.

    This function receives a UserCreate object, creates a UserModel
    instance, and adds it to the database using the UserService.

    Args:
    user: UserCreate object containing the new user details.
    db_session: Database session dependency, provided by the get_db_session function.

    Returns:
    The newly added UserModel object.
    """
    user_service = UserService(db_session=db_session)
    new_user = UserModel(
        name=user.name,
        email=user.email,
        role=user.role,
        password=user.password  # Password hashing should be done separately for security reasons
    )
    added_user = await user_service.add_user(new_user)
    return added_user

@router.put("/{user_id}", response_model=UserModel)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db_session = Depends(get_db_session)
):  
    """
    Endpoint to update an existing user.

    This function receives a UserUpdate object along with a user_id,
    retrieves the existing user from the database, updates the fields,
    and then saves the updated user using the UserService.

    Args:
    user_id: The ID of the user to be updated.
    user: UserUpdate object containing the user update details.
    db_session: Database session dependency, provided by the get_db_session function.

    Returns:
    The updated UserModel object, or raises an HTTPException if the user is not found or update fails.
    """
    user_service = UserService(db_session=db_session)
    existing_user = await user_service.get_users(uuid=user_id)# Assuming this method can handle filtering by ID

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    existing_user = existing_user[0]
    existing_user.name = user.name or existing_user.name
    existing_user.email = user.email or existing_user.email
    existing_user.role = user.role or existing_user.role
    existing_user.password = user.password or existing_user.password  # Password hashing should be done separately

    updated = await user_service.update_user(existing_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )

    return existing_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db_session = Depends(get_db_session)
):  
    """
    Endpoint to delete an existing user.

    This function receives a user_id, retrieves the user from the
    database, and then deletes it using the UserService.

    Args:
    user_id: The UUID of the user to be deleted.
    db_session: Database session dependency, provided by the get_db_session function.

    Returns:
    HTTP 204 No Content status code if successful, or raises an HTTPException if the user is not found or deletion fails.
    """
    user_service = UserService(db_session=db_session)
    existing_user = await user_service.get_users(uuid=user_id)

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:  
        await user_service.delete_user(existing_user[0].uuid)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )

    return None

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db_session: Session = Depends(get_db_session)):
    """
    Endpoint for user login and token generation.

    This function verifies the user credentials and returns an access token.

    Args:
    form_data: OAuth2PasswordRequestForm containing the user credentials.
    db_session: Database session dependency, provided by the get_db_session function.

    Returns:
    A dictionary containing the access token and token type, or raises an HTTPException if credentials are invalid.
    """
    user_service = UserService(db_session=db_session)
    user = await user_service.verify_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthUtil.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected-route", dependencies=[Depends(get_current_user)])
async def protected_route():
    """
    Endpoint for a protected route.

    This function demonstrates an endpoint that requires user authentication
    by ensuring the current user is successfully retrieved by the get_current_user dependency.

    Returns:
    A dictionary with a message indicating that this is a protected route.
    """
    return {"message": "This is a protected route"}
