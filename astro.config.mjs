import { defineConfig } from "astro/config";
import { unified } from "@astrojs/markdown-remark";
import starlight from "@astrojs/starlight";
import starlightImageZoom from "starlight-image-zoom";
import { starlightBasePath } from "starlight-base-path";
import mermaid from "astro-mermaid";

// Custom domain root: https://s3-express-hot-lookup-walkthrough.johna.kiwi
const site = "https://s3-express-hot-lookup-walkthrough.johna.kiwi";
const base = "/";

export default defineConfig({
  site,
  base,
  // starlight-image-zoom and astro-mermaid need the remark/rehype pipeline.
  markdown: {
    processor: unified(),
  },
  integrations: [
    mermaid(),
    starlight({
      title: "S3 Express Hot Lookup Walkthrough",
      favicon: "/favicon.svg",
      description:
        "Guided CLI lab for Amazon S3 Express One Zone shared hot lookup — same-AZ bakeoff vs Standard with a built-in harness dashboard.",
      customCss: [
        "./src/styles/patina-tokens.css",
        "./src/styles/splash-overrides.css",
      ],
      components: {
        ThemeSelect: "./src/components/ThemeSelect.astro",
        Head: "./src/components/Head.astro",
      },
      head: [
        {
          tag: "meta",
          attrs: {
            property: "og:image",
            content: `${site}${base}og-image.png`,
          },
        },
        {
          tag: "meta",
          attrs: {
            property: "og:image:alt",
            content:
              "S3 Express Hot Lookup Walkthrough — VPC, Express bakeoff, harness, teardown",
          },
        },
        {
          tag: "meta",
          attrs: {
            name: "twitter:image",
            content: `${site}${base}og-image.png`,
          },
        },
      ],
      plugins: [starlightBasePath(), starlightImageZoom()],
      social: [
        {
          icon: "github",
          label: "Source Repository",
          href: "https://github.com/jajera/s3-express-hot-lookup-walkthrough",
        },
      ],
      editLink: {
        baseUrl:
          "https://github.com/jajera/s3-express-hot-lookup-walkthrough/edit/main/",
      },
      lastUpdated: true,
      pagination: true,
      sidebar: [
        { label: "Home", link: "/" },
        { label: "Install tooling", slug: "install-tooling" },
        { label: "Prerequisites", slug: "prerequisites" },
        { label: "Architecture", slug: "architecture" },
        {
          label: "Walkthrough",
          items: [
            { label: "CLI overview", slug: "cli" },
            {
              label: "Setup",
              items: [
                { label: "Build harness image", slug: "cli/setup/image" },
                { label: "Create the VPC", slug: "cli/setup/vpc" },
                { label: "Create the buckets", slug: "cli/setup/buckets" },
                { label: "IAM and EC2", slug: "cli/setup/iam-and-ec2" },
              ],
            },
            { label: "Seed and run harness", slug: "cli/harness" },
            { label: "Read the dashboard", slug: "cli/dashboard" },
            { label: "Tear down", slug: "cli/teardown" },
          ],
        },
        {
          label: "Guidance",
          items: [
            {
              label: "Where Express fits",
              slug: "guidance/where-express-fits",
            },
          ],
        },
        {
          label: "Reference",
          items: [
            { label: "Commands", slug: "reference/commands" },
            { label: "Costs and limits", slug: "reference/costs-and-limits" },
            { label: "Troubleshooting", slug: "reference/troubleshooting" },
            {
              label: "Cleanup checklist",
              slug: "reference/cleanup-checklist",
            },
          ],
        },
      ],
    }),
  ],
});
