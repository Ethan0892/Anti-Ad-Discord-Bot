"""
Admin utilities for managing the Anti-Ad Bot
Includes functions for managing training data, checking logs, etc.
"""

import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database


class AdminUtils:
    """Admin utilities for bot management."""
    
    def __init__(self):
        self.db = Database()
        self.training_data_path = Path("Training-Data")
    
    def list_muted_users(self, include_appeals=False):
        """List all muted users."""
        muted = self.db.get_all_muted_users()
        
        print("\n" + "="*80)
        print("MUTED USERS")
        print("="*80)
        
        if not muted:
            print("No muted users.")
            return
        
        for i, user in enumerate(muted, 1):
            print(f"\n{i}. {user['username']} (ID: {user['user_id']})")
            print(f"   Muted: {user['muted_at']}")
            print(f"   Reason: {user['reason']}")
            print(f"   Matched: {user['matched_image']}")
            print(f"   Confidence: {user['confidence']:.2%}")
            print(f"   Appeal Status: {user['appeal_status']}")
    
    def list_appeals(self, status=None):
        """List appeals."""
        appeals = self.db.data['appeals']
        
        if status:
            appeals = [a for a in appeals if a['status'] == status]
        
        print("\n" + "="*80)
        print(f"APPEALS {'(Status: ' + status + ')' if status else ''}")
        print("="*80)
        
        if not appeals:
            print("No appeals found.")
            return
        
        for i, appeal in enumerate(appeals):
            print(f"\n{i}. {appeal['username']} (ID: {appeal['user_id']})")
            print(f"   Submitted: {appeal['submitted_at']}")
            print(f"   Status: {appeal['status']}")
            print(f"   Reason: {appeal['reason']}")
    
    def export_stats(self, filename="bot_stats.json"):
        """Export bot statistics."""
        muted = self.db.get_all_muted_users()
        appeals = self.db.get_pending_appeals()
        
        stats = {
            'exported_at': datetime.utcnow().isoformat(),
            'total_muted_users': len(muted),
            'pending_appeals': len(appeals),
            'muted_users': muted,
            'appeals': appeals
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Stats exported to {filename}")
    
    def import_training_images(self, directory):
        """Import training images from directory."""
        source_dir = Path(directory)
        target_dir = self.training_data_path
        
        if not source_dir.exists():
            print(f"❌ Source directory not found: {source_dir}")
            return
        
        target_dir.mkdir(exist_ok=True)
        
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
        imported = 0
        
        for img_file in source_dir.iterdir():
            if img_file.suffix.lower() in image_extensions:
                try:
                    # Copy to training data
                    target_file = target_dir / img_file.name
                    with open(img_file, 'rb') as src:
                        with open(target_file, 'wb') as dst:
                            dst.write(src.read())
                    imported += 1
                    print(f"  ✓ Imported: {img_file.name}")
                except Exception as e:
                    print(f"  ✗ Error importing {img_file.name}: {e}")
        
        print(f"\n✅ Imported {imported} training image(s)")
    
    def view_logs(self, lines=50):
        """View recent bot logs."""
        log_file = Path("bot.log")
        
        if not log_file.exists():
            print("❌ No log file found.")
            return
        
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # Get last N lines
        recent = all_lines[-lines:]
        
        print("\n" + "="*80)
        print(f"RECENT LOGS (last {len(recent)} lines)")
        print("="*80 + "\n")
        
        for line in recent:
            print(line, end='')
    
    def clean_old_data(self, days=90):
        """Clean old data from database."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        removed = 0
        
        # Clean muted users with denied appeals
        muted_copy = dict(self.db.data['muted_users'])
        for user_id, user_data in muted_copy.items():
            if user_data['appeal_status'] == 'denied':
                muted_date = datetime.fromisoformat(user_data['muted_at'])
                if muted_date < cutoff_date:
                    del self.db.data['muted_users'][user_id]
                    removed += 1
        
        # Clean old denied appeals
        appeals_copy = self.db.data['appeals'].copy()
        for appeal in appeals_copy:
            if appeal['status'] == 'denied':
                appeal_date = datetime.fromisoformat(appeal['submitted_at'])
                if appeal_date < cutoff_date:
                    self.db.data['appeals'].remove(appeal)
                    removed += 1
        
        self.db.save()
        print(f"✅ Cleaned {removed} old record(s)")


def main():
    """Main admin utility interface."""
    utils = AdminUtils()
    
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║      Discord Anti-Ad Bot - Admin Utilities                    ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    while True:
        print("\nOptions:")
        print("1. List muted users")
        print("2. List appeals")
        print("3. View logs")
        print("4. Export statistics")
        print("5. Clean old data")
        print("6. Import training images")
        print("0. Exit")
        
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == "1":
            utils.list_muted_users()
        elif choice == "2":
            status = input("Filter by status (pending/approved/denied) or leave empty: ").strip() or None
            utils.list_appeals(status)
        elif choice == "3":
            lines = input("Number of lines to show [50]: ").strip() or "50"
            try:
                utils.view_logs(int(lines))
            except ValueError:
                print("❌ Invalid number")
        elif choice == "4":
            filename = input("Export filename [bot_stats.json]: ").strip() or "bot_stats.json"
            utils.export_stats(filename)
        elif choice == "5":
            days = input("Delete records older than (days) [90]: ").strip() or "90"
            try:
                utils.clean_old_data(int(days))
            except ValueError:
                print("❌ Invalid number")
        elif choice == "6":
            directory = input("Source directory path: ").strip()
            utils.import_training_images(directory)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
