# models/social.py
"""
ماژول شبکه اجتماعی متیسما
شامل: پست‌ها، فالو/کانکشن، لایک، کامنت
"""
from . import db
from datetime import datetime
from sqlalchemy import text


class Follow(db.Model):
    """
    سیستم دنبال کردن کاربران (Graph/Connections)
    کاربر A کاربر B را دنبال می‌کند
    """
    __tablename__ = 'follow'
    
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # TODO: Translate -  سطح Access: public فقط Post‌های عمومی، connection Access Complete‌تر
    connection_type = db.Column(db.String(20), default='public')  # public, connection, premium
    
    # TODO: Translate -  جلوگیری از فالو تکراری
    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='uq_follow_user_pair'),
    )
    
    # Relationships
    follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following')
    following = db.relationship('User', foreign_keys=[following_id], back_populates='followers')
    
    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.following_id}>"
    
    @classmethod
    def is_following(cls, follower_id, following_id):
        """TODO: Translate - Check اینکه آیا User A User B را دنبال می‌کند"""
        return cls.query.filter_by(
            follower_id=follower_id,
            following_id=following_id
        ).first() is not None
    
    @classmethod
    def get_followers_count(cls, user_id):
        """TODO: Translate - تعداد دنبال‌کنندگان یک User"""
        return cls.query.filter_by(following_id=user_id).count()
    
    @classmethod
    def get_following_count(cls, user_id):
        """TODO: Translate - تعداد افرادی که User دنبال می‌کند"""
        return cls.query.filter_by(follower_id=user_id).count()


class Post(db.Model):
    """
    پست‌های فید اخبار (The Feed)
    قلب تپنده شبکه اجتماعی
    """
    __tablename__ = 'post'
    
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # TODO: Translate -  محتوا
    content = db.Column(db.Text, nullable=False)  # TODO: Translate -  متن Post
    visibility = db.Column(db.String(20), default='public')  # public, followers_only, private
    
    # TODO: Translate -  رسانه‌ها (JSON برای Save List File‌ها)
    # TODO: Translate -  مثال: {"images": ["url1", "url2"], "files": ["file1.pdf"]}
    media = db.Column(db.JSON, default=dict)
    
    # TODO: Translate -  تگ‌کRejectن Productات یا شرکت‌ها
    tagged_products = db.Column(db.JSON, default=list)  #  List product_ids
    tagged_companies = db.Column(db.JSON, default=list)  #  List company_ids
    
    # TODO: Translate -  آمار تعاملات (برای بهینه‌سازی، از Redis هم می‌توان استفاده کReject)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    #  Status
    is_pinned = db.Column(db.Boolean, default=False)  # TODO: Translate -  سنجاق شده توسط ادمین
    is_featured = db.Column(db.Boolean, default=False)  # TODO: Translate -  Post برگزیده پلتفرم
    is_edited = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan', lazy='dynamic')
    # TODO: Translate -  likes relationship Delete شد چون در Model Like با primaryjoin Orderی تعریف شده است
    
    def __repr__(self):
        return f"<Post {self.id} by {self.author_id}>"
    
    def to_dict(self, include_author=True):
        """TODO: Translate - تبدیل Post به Dictionary برای API"""
        data = {
            'id': self.id,
            'content': self.content,
            'visibility': self.visibility,
            'media': self.media or {},
            'tagged_products': self.tagged_products or [],
            'tagged_companies': self.tagged_companies or [],
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'views_count': self.views_count,
            'is_pinned': self.is_pinned,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_author and self.author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'company_name': self.author.company_name,
                'role': self.author.role.value if self.author.role else None,
                'role_display': self.author.role_display_name,
            }
            
            # TODO: Translate -  اضافه کRejectن Information پروFile اگر موجود باشد
            if hasattr(self.author, 'profile') and self.author.profile:
                profile = self.author.profile
                data['author']['bio'] = profile.bio
                data['author']['website'] = profile.website
        
        return data
    
    @classmethod
    def get_feed_for_user(cls, user_id, limit=50, include_featured=True):
        """
        دریافت فید اخبار برای یک کاربر
        الگوریتم ساده: پست‌های کسانی که فالو کرده + پست‌های برگزیده
        """
        # TODO: Translate -  کوئری برای پیدا کRejectن Userانی که این User دنبال می‌کند
        following_subquery = db.session.query(Follow.following_id).filter_by(
            follower_id=user_id
        ).subquery()
        
        # TODO: Translate -  Post‌های Userان فالو شده
        followed_posts = cls.query.filter(
            cls.author_id.in_(following_subquery),
            cls.visibility.in_(['public', 'followers_only'])
        )
        
        # TODO: Translate -  Post‌های برگزیده پلتفرم
        if include_featured:
            featured_posts = cls.query.filter_by(is_featured=True, visibility='public')
            # TODO: Translate -  ترکیب دو کوئری (با Delete تکراری‌ها)
            all_posts = followed_posts.union(featured_posts)
        else:
            all_posts = followed_posts
        
        # TODO: Translate -  مرتب‌سازی بر اساس Time (جدیدترین اول)
        return all_posts.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_public_posts(cls, limit=50):
        """TODO: Translate - دریافت Post‌های عمومی برای View در پروFile عمومی"""
        return cls.query.filter_by(visibility='public').order_by(
            cls.created_at.desc()
        ).limit(limit).all()


class Comment(db.Model):
    """
    کامنت‌های پست‌ها (Engagement)
    """
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # TODO: Translate -  برای Response به کامنت‌ها
    
    content = db.Column(db.Text, nullable=False)
    
    # TODO: Translate -  آمار
    likes_count = db.Column(db.Integer, default=0)
    
    #  Status
    is_edited = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)  # TODO: Translate -  نرم‌دیلیت برای حفظ زنجیره مکالمه
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = db.relationship('Post', back_populates='comments')
    author = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"
    
    def to_dict(self, include_author=True):
        """TODO: Translate - تبدیل کامنت به Dictionary"""
        data = {
            'id': self.id,
            'post_id': self.post_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'likes_count': self.likes_count,
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'replies_count': len(self.replies) if self.replies else 0,
        }
        
        if include_author and self.author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'company_name': self.author.company_name,
                'role': self.author.role.value if self.author.role else None,
            }
        
        return data


class Like(db.Model):
    """
    لایک پست‌ها و کامنت‌ها (Engagement)
    استفاده از JSON برای پشتیبانی از لایک هم پست و هم کامنت
    """
    __tablename__ = 'like'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # TODO: Translate -  Type آیتم موReject Like: 'post' یا 'comment'
    target_type = db.Column(db.String(20), nullable=False)  # TODO: Translate -  'post' یا 'comment'
    target_id = db.Column(db.Integer, nullable=False, index=True)  # TODO: Translate -  post_id یا comment_id
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # TODO: Translate -  جلوگیری از Like تکراری
    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_type', 'target_id', name='uq_like_user_target'),
    )
    
    # Relationships
    user = db.relationship('User', backref='likes')
    # TODO: Translate -  post relationship با primaryjoin Orderی برای پلی‌مورفیک
    post = db.relationship('Post', 
                          primaryjoin="and_(Like.target_type=='post', Like.target_id==Post.id)",
                          foreign_keys=[target_id],
                          viewonly=True)
    
    def __repr__(self):
        return f"<Like {self.user_id} on {self.target_type}:{self.target_id}>"
    
    @classmethod
    def is_liked(cls, user_id, target_type, target_id):
        """TODO: Translate - Check اینکه آیا User آیتم را Like کRejectه است"""
        return cls.query.filter_by(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id
        ).first() is not None
    
    @classmethod
    def get_likes_count(cls, target_type, target_id):
        """TODO: Translate - تعداد Like‌های یک آیتم"""
        return cls.query.filter_by(
            target_type=target_type,
            target_id=target_id
        ).count()


# TODO: Translate -  Update relationshipهای User
def update_user_relationships():
    """
    افزودن relationshipهای جدید به کلاس User
    این تابع باید بعد از ایمپورت تمام مدل‌ها صدا زده شود
    """
    from .user import User
    
    # TODO: Translate -  اضافه کRejectن relationshipهای social به User
    if not hasattr(User, 'posts'):
        User.posts = db.relationship('Post', back_populates='author', cascade='all, delete-orphan', lazy='dynamic')
    
    if not hasattr(User, 'following'):
        User.following = db.relationship('Follow', foreign_keys='Follow.follower_id', 
                                        back_populates='follower', cascade='all, delete-orphan')
    
    if not hasattr(User, 'followers'):
        User.followers = db.relationship('Follow', foreign_keys='Follow.following_id', 
                                        back_populates='following', cascade='all, delete-orphan')
    
    # TODO: Translate -  Propertyهای کمکی
    if not hasattr(User, 'followed_posts'):
        @property
        def followed_posts(self):
            """TODO: Translate - دریافت Post‌های Userان فالو شده"""
            following_ids = [f.following_id for f in self.following]
            return Post.query.filter(Post.author_id.in_(following_ids)).order_by(Post.created_at.desc())
        
        User.followed_posts = followed_posts
    
    if not hasattr(User, 'followers_count'):
        @property
        def followers_count(self):
            """TODO: Translate - تعداد دنبال‌کنندگان"""
            return Follow.get_followers_count(self.id)
        
        User.followers_count = followers_count
    
    if not hasattr(User, 'following_count'):
        @property
        def following_count(self):
            """TODO: Translate - تعداد افرادی که دنبال می‌کند"""
            return Follow.get_following_count(self.id)
        
        User.following_count = following_count


# Helper functions
def create_sample_posts(admin_user, sample_data):
    """
    ایجاد پست‌های نمونه برای پر کردن اولیه پلتفرم
    استراتژی محتوای اولیه از CONTEXT_MASTER_BRIEF
    """
    posts = []
    for data in sample_data:
        post = Post(
            author_id=admin_user.id,
            content=data['content'],
            visibility='public',
            is_featured=data.get('is_featured', False),
            media=data.get('media', {}),
            tagged_companies=data.get('tagged_companies', [])
        )
        db.session.add(post)
        posts.append(post)
    
    db.session.commit()
    return posts
