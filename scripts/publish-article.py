#!/usr/bin/env python3
"""
Publish article to Astro blog
Usage: python publish-article.py
"""

import os
import sys
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path


def create_slug(title):
    """Create URL-safe slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')[:60]


def strip_duplicate_title(content, title):
    """
    Remove first H1 heading if it matches the title
    This prevents duplicate H1 tags (one in frontmatter, one in content)
    """
    # Match first H1 (# Title or # Title with trailing #)
    pattern = r'^#\s+(.+?)(?:\s+#*)?\s*\n'
    match = re.match(pattern, content.strip(), re.MULTILINE)

    if match:
        heading_text = match.group(1).strip()
        # Remove if it matches title (case-insensitive)
        if heading_text.lower() == title.lower():
            content = re.sub(pattern, '', content.strip(), count=1)
            return content.lstrip()

    return content


def convert_lists_to_paragraphs(content):
    """
    Convert markdown lists to bullet paragraph format for Medium compatibility

    Medium's importer doesn't handle <ul><li> well, so we convert:
    - Item 1
    - Item 2

    To:
    • Item 1

    • Item 2

    (with blank lines so each bullet becomes a separate <p> tag)
    """
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a list item (unordered: -, *, + or ordered: 1. 2. etc)
        if re.match(r'^[\s]*[-\*\+]\s+(.+)', line):
            # Unordered list item
            match = re.match(r'^[\s]*([-\*\+])\s+(.+)', line)
            if match:
                item_text = match.group(2)
                # Use bullet point instead of dash
                result.append(f'• {item_text}')
                # Add blank line after each bullet so it becomes separate <p> in HTML
                result.append('')
        elif re.match(r'^[\s]*\d+\.\s+(.+)', line):
            # Ordered list item - keep the number
            match = re.match(r'^[\s]*(\d+)\.\s+(.+)', line)
            if match:
                number = match.group(1)
                item_text = match.group(2)
                result.append(f'{number}. {item_text}')
                # Add blank line after each numbered item
                result.append('')
        else:
            # Not a list item, keep as is
            result.append(line)

        i += 1

    return '\n'.join(result)


def make_images_absolute(content, blog_url):
    """
    Convert relative image URLs to absolute URLs
    This prevents broken images when Medium imports the article
    """
    # Pattern 1: Markdown images with relative paths: ![alt](/path/to/image.png)
    def replace_md_image(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        if img_path.startswith('/'):
            return f'![{alt_text}]({blog_url}{img_path})'
        return match.group(0)  # Leave absolute URLs unchanged

    content = re.sub(r'!\[([^\]]*)\]\((/[^)]+)\)', replace_md_image, content)

    # Pattern 2: HTML img tags with relative src: <img src="/path/to/image.png">
    def replace_html_image(match):
        before = match.group(1)
        img_path = match.group(2)
        after = match.group(3)
        if img_path.startswith('/'):
            return f'{before}{blog_url}{img_path}{after}'
        return match.group(0)

    content = re.sub(r'(<img[^>]+src=["\'])(/[^"\']+)(["\'][^>]*>)', replace_html_image, content)

    return content


def publish_article(article_data):
    """
    Publish article to Astro blog

    Args:
        article_data (dict): {
            'title': str,
            'content': str,  # Markdown content
            'tags': list[str],
            'description': str
        }

    Returns:
        dict: {'success': bool, 'url': str, 'filepath': str}
    """

    # Extract data
    title = article_data.get('title', 'Untitled')
    content = article_data.get('content', '')
    tags = article_data.get('tags', [])
    description = article_data.get('description', '')[:160]  # Meta description limit

    # Get blog URL for absolute image paths
    blog_url = os.getenv('BLOG_URL', 'http://localhost:4321')

    # Remove duplicate H1 if present (template already renders title as H1)
    content = strip_duplicate_title(content, title)

    # Convert markdown lists to bullet paragraphs for Medium compatibility
    content = convert_lists_to_paragraphs(content)

    # Convert relative image URLs to absolute URLs
    # This prevents broken images when Medium imports the article
    content = make_images_absolute(content, blog_url)

    # Create slug and filename
    slug = create_slug(title)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{slug}.md"

    # Create frontmatter
    frontmatter = f"""---
title: "{title}"
description: "{description}"
pubDate: {datetime.now().isoformat()}
tags: {json.dumps(tags[:5])}
draft: false
---

"""

    # Combine frontmatter + content
    full_content = frontmatter + content

    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    posts_dir = repo_root / "src" / "content" / "blog"
    posts_dir.mkdir(parents=True, exist_ok=True)

    filepath = posts_dir / filename

    # Write file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)

        print(f"✓ Article written to: {filepath}")

        # Git operations
        os.chdir(repo_root)

        subprocess.run(['git', 'add', str(filepath)], check=True)
        subprocess.run(['git', 'commit', '-m', f'Add article: {title}'], check=True)
        subprocess.run(['git', 'push'], check=True)

        print("✓ Pushed to GitHub")

        # Construct URL
        article_url = f"{blog_url}/blog/{slug}"

        return {
            'success': True,
            'url': article_url,
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
    if len(sys.argv) > 1:
        # Read from JSON argument
        article_data = json.loads(sys.argv[1])
    else:
        # Interactive mode
        print("Enter article details:")
        title = input("Title: ")
        description = input("Description: ")
        tags = input("Tags (comma-separated): ").split(',')
        content = input("Content (or path to .md file): ")

        if Path(content).exists():
            with open(content, 'r') as f:
                content = f.read()

        article_data = {
            'title': title,
            'description': description,
            'tags': [t.strip() for t in tags],
            'content': content
        }

    result = publish_article(article_data)
    print(json.dumps(result, indent=2))
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
