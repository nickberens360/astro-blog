#!/usr/bin/env python3
"""
Publish Medium-optimized HTML to blog
Creates a standalone HTML file that Medium's import can parse correctly
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path


def create_slug(title):
    """Create URL-safe slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')[:60]


def publish_medium_html(html_content: str, article_data: dict) -> dict:
    """
    Publish Medium-optimized HTML file to blog

    Args:
        html_content: Complete HTML document optimized for Medium
        article_data: Original article metadata for slug generation

    Returns:
        dict: {'success': bool, 'url': str, 'filepath': str}
    """
    title = article_data.get('title', 'Untitled')
    blog_url = os.getenv('BLOG_URL', 'http://localhost:4321')

    # Create slug
    slug = create_slug(title)
    filename = f"{slug}-medium.html"

    # Determine paths - use public folder for static HTML
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    medium_dir = repo_root / "public" / "medium-imports"
    medium_dir.mkdir(parents=True, exist_ok=True)

    filepath = medium_dir / filename

    try:
        # Write HTML file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ Medium HTML written to: {filepath}")

        # Git operations
        os.chdir(repo_root)

        subprocess.run(['git', 'add', str(filepath)], check=True)

        # Check if there are changes to commit
        status_result = subprocess.run(
            ['git', 'status', '--porcelain', str(filepath)],
            capture_output=True,
            text=True
        )

        if status_result.stdout.strip():
            # There are changes, commit them
            subprocess.run(
                ['git', 'commit', '-m', f'Add Medium import HTML: {title}'],
                check=True
            )
            subprocess.run(['git', 'push'], check=True)
            print("✓ Pushed to GitHub")
        else:
            # No changes, file already exists and is unchanged
            print("✓ File already up to date (no changes to commit)")

        # Construct URL
        medium_url = f"{blog_url}/medium-imports/{filename}"

        return {
            'success': True,
            'url': medium_url,
            'filepath': str(filepath),
            'slug': slug
        }

    except Exception as e:
        print(f"✗ Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """CLI entry point"""
    if len(sys.argv) < 3:
        print("Usage: python publish-medium-html.py '<html_content>' '<json_article_data>'")
        sys.exit(1)

    html_content = sys.argv[1]
    article_data = json.loads(sys.argv[2])

    result = publish_medium_html(html_content, article_data)
    print(json.dumps(result, indent=2))
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
