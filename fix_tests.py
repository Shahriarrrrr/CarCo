"""
Script to fix all test files with correct field names
"""
import os
import re

# Define all test files that need updating
test_files = [
    'forum/tests/test_models.py',
    'forum/tests/test_views.py',
    'cars/tests.py',
    'parts/tests.py',
    'payments/tests.py',
    'messaging/tests.py',
    'locations/tests.py',
    'comments/tests.py',
    'ratings/tests.py',
    'notifications/tests.py',
    'integration_tests.py',
]

def fix_file(filepath):
    """Fix user creation calls in test files"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace full_name= with first_name= and last_name=
        # Pattern: User.objects.create_user(..., full_name="Name", ...)
        pattern = r'(User\.objects\.create_user\([^)]*?)full_name\s*=\s*["\']([^"\']+)["\']'
        
        def replace_full_name(match):
            prefix = match.group(1)
            name = match.group(2)
            # Split name into first and last
            parts = name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = ' '.join(parts[1:])
            else:
                first = name
                last = "User"
            return f'{prefix}first_name="{first}", last_name="{last}"'
        
        content = re.sub(pattern, replace_full_name, content)
        
        # Replace SellerRating with Rating
        content = content.replace('SellerRating', 'Rating')
        content = content.replace('from ratings.models import Review, Rating, ReviewVote', 
                                'from ratings.models import Review, Rating, ReviewVote')
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
            return True
        else:
            print(f"⏭️  No changes needed: {filepath}")
            return False
    except FileNotFoundError:
        print(f"❌ Not found: {filepath}")
        return False
    except Exception as e:
        print(f"❌ Error in {filepath}: {e}")
        return False

if __name__ == '__main__':
    fixed_count = 0
    for test_file in test_files:
        if fix_file(test_file):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")
