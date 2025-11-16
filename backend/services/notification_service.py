from datetime import datetime
from models import db, Notification, User


class NotificationService:
    """Service for managing notifications"""
    
    def send_face_detection_notification(self, detected_user_id, uploader_id, content_id, is_story=False):
        """
        Send notification when someone's face is detected in a post/story
        
        Args:
            detected_user_id: ID of the user whose face was detected
            uploader_id: ID of the user who uploaded the content
            content_id: ID of the post or story
            is_story: Boolean indicating if it's a story or post
        """
        try:
            # Don't send notification if user uploaded their own photo
            if detected_user_id == uploader_id:
                return
            
            uploader = User.query.get(uploader_id)
            if not uploader:
                return
            
            content_type = "story" if is_story else "post"
            message = f"{uploader.username} posted a {content_type} that includes your face. Please review and approve."
            
            notification = Notification(
                user_id=detected_user_id,
                type='face_detected',
                message=message,
                related_user_id=uploader_id,
                related_post_id=content_id if not is_story else None,
                related_story_id=content_id if is_story else None
            )
            
            db.session.add(notification)
            db.session.commit()
            
            print(f"Notification sent to user {detected_user_id}")
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            db.session.rollback()
    
    def send_approval_notification(self, post_owner_id, approver_id, content_id, is_story=False, approved=True):
        """
        Send notification when someone approves/rejects appearing in a post/story
        
        Args:
            post_owner_id: ID of the user who owns the post/story
            approver_id: ID of the user who approved/rejected
            content_id: ID of the post or story
            is_story: Boolean indicating if it's a story or post
            approved: Boolean indicating if approved or rejected
        """
        try:
            approver = User.query.get(approver_id)
            if not approver:
                return
            
            content_type = "story" if is_story else "post"
            action = "approved" if approved else "rejected"
            message = f"{approver.username} has {action} appearing in your {content_type}."
            
            notification = Notification(
                user_id=post_owner_id,
                type='approval_response',
                message=message,
                related_user_id=approver_id,
                related_post_id=content_id if not is_story else None,
                related_story_id=content_id if is_story else None
            )
            
            db.session.add(notification)
            db.session.commit()
            
        except Exception as e:
            print(f"Error sending approval notification: {str(e)}")
            db.session.rollback()
    
    def get_user_notifications(self, user_id, unread_only=False):
        """
        Get all notifications for a user
        
        Args:
            user_id: ID of the user
            unread_only: If True, only return unread notifications
        
        Returns:
            List of notification dicts
        """
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            notifications = query.order_by(Notification.created_at.desc()).all()
            
            return [notif.to_dict() for notif in notifications]
            
        except Exception as e:
            print(f"Error getting notifications: {str(e)}")
            return []
    
    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                notification.is_read = True
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            print(f"Error marking notification as read: {str(e)}")
            db.session.rollback()
            return False
    
    def mark_all_read(self, user_id):
        """Mark all notifications as read for a user"""
        try:
            Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Error marking all notifications as read: {str(e)}")
            db.session.rollback()
            return False
    
    def delete_notification(self, notification_id):
        """Delete a notification"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                db.session.delete(notification)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting notification: {str(e)}")
            db.session.rollback()
            return False
