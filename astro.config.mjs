// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import netlify from '@astrojs/netlify';
import { defineConfig } from 'astro/config';
import { rehypeHeadingIds } from '@astrojs/markdown-remark';
import rehypeRemoveCodeClasses from './rehype-remove-code-classes.mjs';

// https://astro.build/config
export default defineConfig({
	site: 'https://example.com',
	output: 'static',
	adapter: netlify(),
	integrations: [mdx(), sitemap()],
	markdown: {
		syntaxHighlight: false, // Disable syntax highlighting for Medium import compatibility
		rehypePlugins: [
			rehypeHeadingIds, // Add IDs first (so we control the order)
			rehypeRemoveCodeClasses // Then strip them along with code classes
		],
	},
});
