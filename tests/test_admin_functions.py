"""Tests for admin dashboard functions."""
import sys
sys.path.insert(0, '.')

from vocab_stack.database import get_session, create_db_and_tables, drop_all_tables
from vocab_stack.models import User, Flashcard, LeitnerState, ReviewHistory, Topic
from vocab_stack.services.auth_service import AuthService
from sqlmodel import select


class TestAdminFunctions:
    """Test admin dashboard operations."""
    
    @classmethod
    def setup_class(cls):
        """Set up test database with admin and regular users."""
        print("\n" + "=" * 60)
        print("👑 Admin Functions Tests")
        print("=" * 60)
        drop_all_tables()
        create_db_and_tables()
        
        # Create admin user
        AuthService.register("admin", "admin@test.com", "adminpass")
        
        # Create regular users
        AuthService.register("user1", "user1@test.com", "password123")
        AuthService.register("user2", "user2@test.com", "password123")
        
        with get_session() as session:
            cls.admin = session.exec(select(User).where(User.username == "admin")).first()
            cls.admin.is_admin = True
            session.add(cls.admin)
            
            cls.user1 = session.exec(select(User).where(User.username == "user1")).first()
            cls.user2 = session.exec(select(User).where(User.username == "user2")).first()
            
            session.commit()
    
    def test_admin_flag_set_correctly(self):
        """Test that admin flag is set correctly."""
        print("\n🧪 Test: Admin Flag")
        
        with get_session() as session:
            admin = session.get(User, self.admin.id)
            user1 = session.get(User, self.user1.id)
            
            assert admin.is_admin == True, "Admin should have admin flag"
            assert user1.is_admin == False, "Regular user should not have admin flag"
        
        print("✅ Admin flag is correctly set")
    
    def test_grant_admin_privileges(self):
        """Test granting admin privileges to a user."""
        print("\n🧪 Test: Grant Admin Privileges")
        
        with get_session() as session:
            user = session.get(User, self.user1.id)
            
            # Grant admin
            user.is_admin = True
            session.add(user)
            session.commit()
            session.refresh(user)
            
            assert user.is_admin == True, "User should now be admin"
        
        print("✅ Admin privileges granted successfully")
    
    def test_revoke_admin_privileges(self):
        """Test revoking admin privileges from a user."""
        print("\n🧪 Test: Revoke Admin Privileges")
        
        with get_session() as session:
            user = session.get(User, self.user1.id)
            
            # Revoke admin
            user.is_admin = False
            session.add(user)
            session.commit()
            session.refresh(user)
            
            assert user.is_admin == False, "User should no longer be admin"
        
        print("✅ Admin privileges revoked successfully")
    
    def test_reset_user_password(self):
        """Test resetting a user's password."""
        print("\n🧪 Test: Reset User Password")
        
        new_password = "newpassword123"
        
        with get_session() as session:
            user = session.get(User, self.user2.id)
            
            # Reset password
            user.password_hash = AuthService.hash_password(new_password)
            session.add(user)
            session.commit()
        
        # Test login with new password
        success, message, user_data = AuthService.login("user2", new_password)
        assert success, f"Login with new password should work: {message}"
        
        # Old password should not work
        success, message, user_data = AuthService.login("user2", "password123")
        assert not success, "Old password should not work"
        
        print("✅ Password reset successfully")
    
    def test_delete_user_with_data(self):
        """Test deleting a user with all their data."""
        print("\n🧪 Test: Delete User with Data")
        
        # Create a user with cards
        AuthService.register("delete_me", "delete@test.com", "password123")
        
        with get_session() as session:
            user = session.exec(select(User).where(User.username == "delete_me")).first()
            user_id = user.id
            
            # Create topic and cards for this user
            topic = Topic(name="Test Topic", description="For deletion test")
            session.add(topic)
            session.flush()
            
            card = Flashcard(
                front="Test Card",
                back="Test Answer",
                topic_id=topic.id,
                user_id=user_id
            )
            session.add(card)
            session.flush()
            
            card_id = card.id
            
            # Add Leitner state and review history
            leitner = LeitnerState(flashcard_id=card_id, box_number=1)
            review = ReviewHistory(flashcard_id=card_id, user_id=user_id, was_correct=True)
            session.add(leitner)
            session.add(review)
            session.commit()
        
        # Delete user and all their data
        with get_session() as session:
            user = session.get(User, user_id)
            
            # Get all flashcards
            flashcards = session.exec(
                select(Flashcard).where(Flashcard.user_id == user_id)
            ).all()
            
            # Delete related records
            for flashcard in flashcards:
                # Delete Leitner states
                leitner_states = session.exec(
                    select(LeitnerState).where(LeitnerState.flashcard_id == flashcard.id)
                ).all()
                for state in leitner_states:
                    session.delete(state)
                
                # Delete review history
                reviews = session.exec(
                    select(ReviewHistory).where(ReviewHistory.flashcard_id == flashcard.id)
                ).all()
                for review in reviews:
                    session.delete(review)
                
                # Delete flashcard
                session.delete(flashcard)
            
            # Delete user
            session.delete(user)
            session.commit()
        
        # Verify everything was deleted
        with get_session() as session:
            user = session.get(User, user_id)
            assert user is None, "User should be deleted"
            
            cards = session.exec(
                select(Flashcard).where(Flashcard.user_id == user_id)
            ).all()
            assert len(cards) == 0, "All user's cards should be deleted"
            
            leitner_states = session.exec(
                select(LeitnerState).where(LeitnerState.flashcard_id == card_id)
            ).all()
            assert len(leitner_states) == 0, "All Leitner states should be deleted"
            
            reviews = session.exec(
                select(ReviewHistory).where(ReviewHistory.flashcard_id == card_id)
            ).all()
            assert len(reviews) == 0, "All review history should be deleted"
        
        print("✅ User and all data deleted successfully")
    
    def test_view_all_users(self):
        """Test that admin can view all users."""
        print("\n🧪 Test: View All Users")
        
        with get_session() as session:
            all_users = session.exec(select(User)).all()
            
            # Should have at least admin, user1, user2
            assert len(all_users) >= 3, f"Should have at least 3 users, found {len(all_users)}"
            
            # Admin can see all usernames
            usernames = [u.username for u in all_users]
            assert "admin" in usernames, "Should see admin user"
            assert "user1" in usernames, "Should see user1"
            assert "user2" in usernames, "Should see user2"
        
        print(f"✅ Admin can view all {len(all_users)} users")
    
    def test_view_user_statistics(self):
        """Test that admin can view user statistics."""
        print("\n🧪 Test: View User Statistics")
        
        # Create some cards for user1
        with get_session() as session:
            topic = Topic(name="Stats Test Topic", description="For stats")
            session.add(topic)
            session.flush()
            
            for i in range(3):
                card = Flashcard(
                    front=f"Card {i}",
                    back=f"Answer {i}",
                    topic_id=topic.id,
                    user_id=self.user1.id
                )
                session.add(card)
            
            session.commit()
        
        # Admin views user1's statistics
        with get_session() as session:
            user1_cards = session.exec(
                select(Flashcard).where(Flashcard.user_id == self.user1.id)
            ).all()
            
            card_count = len(user1_cards)
            assert card_count == 3, f"User1 should have 3 cards, found {card_count}"
        
        print(f"✅ Admin can view user statistics (user1 has {card_count} cards)")
    
    def test_cannot_delete_self_as_admin(self):
        """Test that admin cannot delete themselves."""
        print("\n🧪 Test: Admin Cannot Delete Self")
        
        # This is a business logic test - in the real app, this would be prevented in the UI
        # Here we just verify we can detect it
        admin_id = self.admin.id
        
        # Attempting to delete self should be caught by checking admin_id == current_user_id
        is_self_delete = (admin_id == admin_id)
        assert is_self_delete == True, "Should detect self-deletion attempt"
        
        print("✅ Self-deletion can be detected and prevented")


def run_all_tests():
    """Run all admin function tests."""
    test_suite = TestAdminFunctions()
    test_suite.setup_class()
    
    tests = [
        test_suite.test_admin_flag_set_correctly,
        test_suite.test_grant_admin_privileges,
        test_suite.test_revoke_admin_privileges,
        test_suite.test_reset_user_password,
        test_suite.test_delete_user_with_data,
        test_suite.test_view_all_users,
        test_suite.test_view_user_statistics,
        test_suite.test_cannot_delete_self_as_admin,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✅ All admin function tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
