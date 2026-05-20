# routes/social/routes.py
"""
ماژول路由‌های شبکه اجتماعی متیسما
شامل: پروفایل عمومی، فید اخبار، فالو/آنفالو، لایک، کامنت
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db
from models.user import User, UserProfile
from models.social import Post, Comment, Like, Follow
from datetime import datetime
import pytz

tehran_tz = pytz.timezone('Asia/Tehran')

social_bp = Blueprint('social', __name__, url_prefix='/social')


# ============================================
# ۱. پروفایل عمومی (Public Profile)
# ============================================

@social_bp.route('/profile/<username>')
def public_profile(username):
    """
    نمایش پروفایل عمومی کاربر
    این صفحه برای عموم (حتی بدون لاگین) قابل مشاهده است - SEO Friendly
    """
    # دریافت کاربر از دیتابیس
    profile_user = User.query.filter_by(username=username, is_active=True).first_or_404()
    
    # دریافت پست‌های عمومی کاربر
    profile_posts = Post.query.filter_by(
        author_id=profile_user.id,
        visibility='public'
    ).order_by(Post.created_at.desc()).limit(20).all()
    
    return render_template('users/public_profile.html', 
                         profile_user=profile_user, 
                         profile_posts=profile_posts)


# ============================================
# ۲. سیستم فالو/کانکشن (Graph/Connections)
# ============================================

@social_bp.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    """
    دنبال کردن یک کاربر
    """
    if current_user.id == user_id:
        return jsonify({'error': 'نمی‌توانید خودتان را دنبال کنید'}), 400
    
    user_to_follow = User.query.get_or_404(user_id)
    
    # بررسی اینکه آیا قبلاً فالو کرده است
    existing_follow = Follow.is_following(current_user.id, user_id)
    
    if not existing_follow:
        follow = Follow(
            follower_id=current_user.id,
            following_id=user_id,
            connection_type='public'
        )
        db.session.add(follow)
        db.session.commit()
        
        # ایجاد نوتیفیکیشن برای کاربر دنبال شده
        from models.notification import Notification
        notification = Notification(
            user_id=user_id,
            title='دنبال‌کننده جدید',
            message=f'{current_user.username} شما را دنبال کرد.',
            type='follow',
            actor_id=current_user.id
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'شما {user_to_follow.username} را دنبال کردید.',
            'followers_count': Follow.get_followers_count(user_id)
        })
    else:
        return jsonify({'error': 'شما قبلاً این کاربر را دنبال کرده‌اید'}), 400


@social_bp.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    """
    آنفالو کردن یک کاربر
    """
    if current_user.id == user_id:
        return jsonify({'error': 'نمی‌توانید خودتان را آنفالو کنید'}), 400
    
    # پیدا کردن رکورد فالو
    follow = Follow.query.filter_by(
        follower_id=current_user.id,
        following_id=user_id
    ).first()
    
    if follow:
        db.session.delete(follow)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'کاربر از لیست دنبال‌شونده‌ها حذف شد.',
            'followers_count': Follow.get_followers_count(user_id)
        })
    else:
        return jsonify({'error': 'شما این کاربر را دنبال نمی‌کنید'}), 400


@social_bp.route('/followers/<int:user_id>')
def user_followers(user_id):
    """
    نمایش لیست دنبال‌کنندگان یک کاربر
    """
    user = User.query.get_or_404(user_id)
    followers = Follow.query.filter_by(following_id=user_id).all()
    
    return render_template('users/followers_list.html', 
                         user=user, 
                         followers=followers)


@social_bp.route('/following/<int:user_id>')
def user_following(user_id):
    """
    نمایش لیست افرادی که کاربر دنبال می‌کند
    """
    user = User.query.get_or_404(user_id)
    following = Follow.query.filter_by(follower_id=user_id).all()
    
    return render_template('users/following_list.html', 
                         user=user, 
                         following=following)


# ============================================
# ۳. فید اخبار (The Feed)
# ============================================

@social_bp.route('/feed')
@login_required
def news_feed():
    """
    فید اخبار شخصی‌سازی شده برای کاربر
    نمایش پست‌های کسانی که فالو کرده + پست‌های برگزیده
    """
    # دریافت فید با الگوریتم ساده
    feed_posts = Post.get_feed_for_user(current_user.id, limit=50, include_featured=True)
    
    return render_template('users/feed.html', feed_posts=feed_posts)


@social_bp.route('/post/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """
    ایجاد پست جدید
    """
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        visibility = request.form.get('visibility', 'public')
        
        if not content:
            flash('محتوای پست نمی‌تواند خالی باشد.', 'error')
            return redirect(url_for('social.news_feed'))
        
        # پردازش فایل‌های آپلود شده (در صورت وجود)
        media = {'images': [], 'files': []}
        # TODO: اضافه کردن منطق آپلود فایل
        
        # پردازش تگ‌های محصولات/شرکت‌ها
        tagged_products = []
        tagged_companies = []
        # TODO: اضافه کردن منطق تگ کردن
        
        post = Post(
            author_id=current_user.id,
            content=content,
            visibility=visibility,
            media=media,
            tagged_products=tagged_products,
            tagged_companies=tagged_companies
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('پست شما با موفقیت منتشر شد.', 'success')
        return redirect(url_for('social.public_profile', username=current_user.username))
    
    return render_template('users/create_post.html')


@social_bp.route('/post/<int:post_id>')
def view_post(post_id):
    """
    نمایش یک پست خاص
    """
    post = Post.query.get_or_404(post_id)
    
    # افزایش تعداد بازدید
    post.views_count += 1
    db.session.commit()
    
    # دریافت کامنت‌ها
    comments = Comment.query.filter_by(
        post_id=post_id,
        is_deleted=False
    ).order_by(Comment.created_at.asc()).all()
    
    return render_template('users/post_detail.html', post=post, comments=comments)


@social_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """
    حذف پست (فقط توسط نویسنده یا ادمین)
    """
    post = Post.query.get_or_404(post_id)
    
    if post.author_id != current_user.id and not current_user.is_admin_or_moderator:
        flash('شما مجوز حذف این پست را ندارید.', 'error')
        return redirect(url_for('social.view_post', post_id=post_id))
    
    db.session.delete(post)
    db.session.commit()
    
    flash('پست با موفقیت حذف شد.', 'success')
    return redirect(url_for('social.public_profile', username=post.author.username))


# ============================================
# ۴. تعاملات (Engagement) - لایک و کامنت
# ============================================

@social_bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """
    لایک کردن یک پست
    """
    post = Post.query.get_or_404(post_id)
    
    # بررسی اینکه آیا قبلاً لایک کرده است
    existing_like = Like.is_liked(current_user.id, 'post', post_id)
    
    if not existing_like:
        like = Like(
            user_id=current_user.id,
            target_type='post',
            target_id=post_id
        )
        db.session.add(like)
        
        # افزایش شمارنده لایک
        post.likes_count += 1
        
        # ایجاد نوتیفیکیشن برای نویسنده پست (اگر لایک کننده خودش نیست)
        if post.author_id != current_user.id:
            from models.notification import Notification
            notification = Notification(
                user_id=post.author_id,
                title='لایک جدید',
                message=f'{current_user.username} پست شما را لایک کرد.',
                type='like',
                actor_id=current_user.id,
                related_id=post_id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'likes_count': post.likes_count,
            'is_liked': True
        })
    else:
        # آنلایک کردن
        like = Like.query.filter_by(
            user_id=current_user.id,
            target_type='post',
            target_id=post_id
        ).first()
        
        if like:
            db.session.delete(like)
            post.likes_count -= 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'likes_count': post.likes_count,
                'is_liked': False
            })
    
    return jsonify({'error': 'خطا در عملیات لایک'}), 500


@social_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """
    افزودن کامنت به یک پست
    """
    post = Post.query.get_or_404(post_id)
    
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)  # برای پاسخ به کامنت
    
    if not content:
        flash('متن کامنت نمی‌تواند خالی باشد.', 'error')
        return redirect(url_for('social.view_post', post_id=post_id))
    
    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        content=content,
        parent_id=parent_id
    )
    
    db.session.add(comment)
    
    # افزایش شمارنده کامنت
    post.comments_count += 1
    
    # ایجاد نوتیفیکیشن برای نویسنده پست (اگر کامنت گذار خودش نیست)
    if post.author_id != current_user.id:
        from models.notification import Notification
        notification = Notification(
            user_id=post.author_id,
            title='کامنت جدید',
            message=f'{current_user.username} روی پست شما کامنت گذاشت.',
            type='comment',
            actor_id=current_user.id,
            related_id=post_id
        )
        db.session.add(notification)
    
    # اگر پاسخ به کامنت دیگری است، به صاحب کامنت اصلی هم نوتیفیکیشن بده
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if parent_comment and parent_comment.author_id != current_user.id:
            notification = Notification(
                user_id=parent_comment.author_id,
                title='پاسخ به کامنت',
                message=f'{current_user.username} به کامنت شما پاسخ داد.',
                type='comment_reply',
                actor_id=current_user.id,
                related_id=post_id
            )
            db.session.add(notification)
    
    db.session.commit()
    
    flash('کامنت شما با موفقیت ثبت شد.', 'success')
    return redirect(url_for('social.view_post', post_id=post_id))


@social_bp.route('/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    """
    لایک کردن یک کامنت
    """
    comment = Comment.query.get_or_404(comment_id)
    
    existing_like = Like.is_liked(current_user.id, 'comment', comment_id)
    
    if not existing_like:
        like = Like(
            user_id=current_user.id,
            target_type='comment',
            target_id=comment_id
        )
        db.session.add(like)
        comment.likes_count += 1
        
        # نوتیفیکیشن برای صاحب کامنت
        if comment.author_id != current_user.id:
            from models.notification import Notification
            notification = Notification(
                user_id=comment.author_id,
                title='لایک کامنت',
                message=f'{current_user.username} کامنت شما را لایک کرد.',
                type='like',
                actor_id=current_user.id,
                related_id=comment_id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'likes_count': comment.likes_count,
            'is_liked': True
        })
    else:
        like = Like.query.filter_by(
            user_id=current_user.id,
            target_type='comment',
            target_id=comment_id
        ).first()
        
        if like:
            db.session.delete(like)
            comment.likes_count -= 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'likes_count': comment.likes_count,
                'is_liked': False
            })
    
    return jsonify({'error': 'خطا در عملیات لایک'}), 500


@social_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """
    حذف کامنت (نرم‌دیلیت)
    """
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.author_id != current_user.id and not current_user.is_admin_or_moderator:
        flash('شما مجوز حذف این کامنت را ندارید.', 'error')
        return redirect(url_for('social.view_post', post_id=comment.post_id))
    
    # نرم‌دیلیت برای حفظ زنجیره مکالمه
    comment.is_deleted = True
    comment.content = '[این کامنت حذف شده است]'
    db.session.commit()
    
    # کاهش شمارنده کامنت پست
    comment.post.comments_count -= 1
    db.session.commit()
    
    flash('کامنت حذف شد.', 'success')
    return redirect(url_for('social.view_post', post_id=comment.post_id))


# ============================================
# ۵. API endpoints برای AJAX calls
# ============================================

@social_bp.route('/api/check-follow/<int:user_id>')
@login_required
def check_follow(user_id):
    """
    بررسی وضعیت فالو (API)
    """
    is_following = Follow.is_following(current_user.id, user_id)
    return jsonify({
        'is_following': is_following,
        'followers_count': Follow.get_followers_count(user_id),
        'following_count': Follow.get_following_count(user_id)
    })


@social_bp.route('/api/post/<int:post_id>/stats')
def get_post_stats(post_id):
    """
    دریافت آمار پست (API)
    """
    post = Post.query.get_or_404(post_id)
    is_liked = False
    
    if current_user.is_authenticated:
        is_liked = Like.is_liked(current_user.id, 'post', post_id)
    
    return jsonify({
        'likes_count': post.likes_count,
        'comments_count': post.comments_count,
        'shares_count': post.shares_count,
        'views_count': post.views_count,
        'is_liked': is_liked
    })


# ============================================
# ۶. صفحات کمکی
# ============================================

@social_bp.route('/explore')
def explore():
    """
    کشف پست‌های برگزیده و کاربران پیشنهادی
    """
    featured_posts = Post.query.filter_by(
        is_featured=True,
        visibility='public'
    ).order_by(Post.created_at.desc()).limit(20).all()
    
    # کاربران پیشنهادی (بر اساس TrustScore)
    suggested_users = User.query.join(UserProfile).filter(
        User.is_active == True,
        User.role.value.in_(['producer', 'buyer', 'broker'])
    ).order_by(db.desc(User.trust_score)).limit(10).all() if hasattr(User, 'trust_score') else []
    
    return render_template('users/explore.html', 
                         featured_posts=featured_posts, 
                         suggested_users=suggested_users)
