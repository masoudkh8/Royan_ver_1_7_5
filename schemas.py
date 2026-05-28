# schemas.py
"""
Schemaهای Pydantic برای اعتبارسنجی داده‌ها در APIها
بر اساس CONTEXT_MASTER_BRIEF و مدل‌های کاربری ۱۰ نقش تخصصی
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """TODO: Translate - ۱۰ Role تخصصی اکوSystem متیسما - هماهنگ با models.user.Role"""
    PRODUCER = 'producer'              # TODO: Translate -  تولیدکننده/صادرکننده
    BUYER = 'buyer'                    # TODO: Translate -  واRejectکننده/Purchaseار
    BROKER = 'broker'                  # TODO: Translate -  کارگزار تجاری
    CORPORATE_AGENT = 'corporate_agent' # TODO: Translate -  نماینده شرکتی
    LOGISTICS = 'logistics'            # TODO: Translate -  خدمات لجستیک و بیمه
    LEGAL = 'legal'                    # TODO: Translate -  خدمات حقوقی و انطباق
    TECH_PARTNER = 'tech_partner'      # TODO: Translate -  شریک فناوری
    INVESTOR = 'investor'              # TODO: Translate -  سرمایه‌گذار مالی
    ADMIN = 'admin'                    # TODO: Translate -  مدیریت System
    MODERATOR = 'moderator'            # TODO: Translate -  ناظر محتوا


# ============================================
# Authentication Schemas
# ============================================

class UserRegister(BaseModel):
    """TODO: Translate - اسکمای Registration User با انتخاب Role"""
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.PRODUCER  # Default to PRODUCER as most common core role
    company_name: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """TODO: Translate - اسکمای Login User"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Response Authentication"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str
    is_premium: bool = False


# ============================================
# User Profile Schemas
# ============================================

class UserProfileBase(BaseModel):
    """TODO: Translate - پایه پروFile Userی"""
    full_name: Optional[str] = Field(None, max_length=100)
    headline: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=2000)
    website: Optional[str] = Field(None, max_length=256)
    linkedin: Optional[str] = Field(None, max_length=256)
    twitter: Optional[str] = Field(None, max_length=256)
    skills: Optional[str] = Field(None, max_length=500)
    industries: Optional[str] = Field(None, max_length=500)
    is_public: bool = True
    allow_messages: bool = True


class UserProfileCreate(UserProfileBase):
    """TODO: Translate - Create پروFile جدید"""
    pass


class UserProfileUpdate(BaseModel):
    """TODO: Translate - Update پروFile - تمام Fieldها Optional"""
    full_name: Optional[str] = Field(None, max_length=100)
    headline: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=2000)
    avatar: Optional[str] = Field(None, max_length=256)
    cover_image: Optional[str] = Field(None, max_length=256)
    website: Optional[str] = Field(None, max_length=256)
    linkedin: Optional[str] = Field(None, max_length=256)
    twitter: Optional[str] = Field(None, max_length=256)
    phone_public: Optional[str] = Field(None, max_length=20)
    skills: Optional[str] = Field(None, max_length=500)
    industries: Optional[str] = Field(None, max_length=500)
    trust_score: Optional[int] = None
    badges: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    allow_messages: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)



class UserProfileResponse(UserProfileBase):
    """TODO: Translate - Response پروFile Userی"""
    id: int
    user_id: int
    avatar: Optional[str] = 'default_avatar.png'
    cover_image: Optional[str] = None
    phone_public: Optional[str] = None
    trust_score: int = 0
    badges: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)



# ============================================
# Post Schemas
# ============================================

class PostCreate(BaseModel):
    """TODO: Translate - Create Post جدید"""
    body: str = Field(..., min_length=1, max_length=10000)
    post_type: str = Field(default='text', pattern='^(text|image|article|product_link)$')
    media_url: Optional[str] = Field(None, max_length=512)
    link_url: Optional[str] = Field(None, max_length=512)
    visibility: str = Field(default='public', pattern='^(public|followers_only|private)$')
    related_product_id: Optional[int] = None
    related_article_id: Optional[int] = None


class PostUpdate(BaseModel):
    """Update Post"""
    body: Optional[str] = Field(None, min_length=1, max_length=10000)
    media_url: Optional[str] = Field(None, max_length=512)
    link_url: Optional[str] = Field(None, max_length=512)
    visibility: Optional[str] = Field(None, pattern='^(public|followers_only|private)$')
    
    model_config = ConfigDict(from_attributes=True)



class PostResponse(BaseModel):
    """Response Post"""
    id: int
    body: str
    post_type: str
    media_url: Optional[str] = None
    link_url: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    timestamp: datetime
    author_username: str
    author_role: str
    
    model_config = ConfigDict(from_attributes=True)



# ============================================
# Comment Schemas
# ============================================

class CommentCreate(BaseModel):
    """TODO: Translate - Create کامنت"""
    body: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[int] = None  # TODO: Translate -  برای Response به کامنت دیگر


class CommentResponse(BaseModel):
    """TODO: Translate - Response کامنت"""
    id: int
    body: str
    timestamp: datetime
    author_username: str
    post_id: int
    parent_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)



# ============================================
# Connection/Follow Schemas
# ============================================

class ConnectionResponse(BaseModel):
    """TODO: Translate - Response Status اتصال"""
    follower_id: int
    followed_id: int
    connection_type: str = 'public'
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)



class FollowStatus(BaseModel):
    """TODO: Translate - Status فالو"""
    is_following: bool
    followers_count: int
    following_count: int


# ============================================
# Feed & Engagement Schemas
# ============================================

class FeedPost(PostResponse):
    """TODO: Translate - Post فید با Information تکمیلی"""
    is_liked_by_user: bool = False
    is_following_author: bool = False


class LikeAction(BaseModel):
    """TODO: Translate - اکشن Like"""
    success: bool
    likes_count: int
    is_liked: bool


class CommentAction(BaseModel):
    """TODO: Translate - اکشن کامنت"""
    success: bool
    comment_id: int
    message: str = "کامنت با موفقیت ثبت شد"


# ============================================
# Public Profile Schemas (SEO Friendly)
# ============================================

class PublicProfileResponse(BaseModel):
    """TODO: Translate - پروFile عمومی برای View به عموم (SEO)"""
    username: str
    role: str
    full_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = 'default_avatar.png'
    skills: Optional[str] = None
    industries: Optional[str] = None
    trust_score: int = 0
    badges: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_public: bool = True
    member_since: datetime
    
    model_config = ConfigDict(from_attributes=True)



# ============================================
# Admin & Moderation Schemas
# ============================================

class UserAdminUpdate(BaseModel):
    """TODO: Translate - Update User توسط ادمین"""
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None
    trust_score_override: Optional[int] = Field(None, ge=0, le=1000)
    
    model_config = ConfigDict(from_attributes=True)



class BulkUserAction(BaseModel):
    """TODO: Translate - اکشن گروهی روی Userان"""
    user_ids: List[int]
    action: str  # 'activate', 'deactivate', 'verify', 'assign_role'
    role: Optional[UserRole] = None  # TODO: Translate -  فقط برای assign_role
