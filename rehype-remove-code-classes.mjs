import { visit } from 'unist-util-visit';

/**
 * Rehype plugin to simplify HTML for Medium's import tool
 * Removes classes, attributes, and IDs that confuse Medium's parser
 */
export default function rehypeRemoveCodeClasses() {
  return (tree) => {
    visit(tree, 'element', (node) => {
      // Remove classes from <code> elements
      if (node.tagName === 'code') {
        delete node.properties.className;
        delete node.properties.class;
      }
      // Remove data-language from <pre> elements
      if (node.tagName === 'pre') {
        delete node.properties.dataLanguage;
        delete node.properties['data-language'];
      }
      // Remove id attributes from headings (h1-h6)
      if (/^h[1-6]$/.test(node.tagName)) {
        delete node.properties.id;
      }
    });
  };
}
