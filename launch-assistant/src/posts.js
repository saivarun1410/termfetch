export const IST_TIME_ZONE = "Asia/Kolkata";

export const POSTS = [
  {
    id: "launch",
    day: 1,
    title: "Launch termfetch",
    scheduledAt: "2026-08-18T15:30:00.000Z",
    readiness: "ready",
    body: `Your GitHub profile, but make it neofetch.

I built termfetch—a Python CLI that turns your photo + live GitHub stats into a self-contained SVG for your README.

No hosted image service. Six themes. MIT licensed.

https://github.com/saivarun1410/termfetch`,
    media: {
      type: "video/mp4",
      url: "https://raw.githubusercontent.com/saivarun1410/termfetch/main/assets/termfetch-demo.mp4",
      filename: "termfetch-demo.mp4"
    },
    notes: [
      "Stay available for 60–90 minutes to answer genuine replies.",
      "Pin the launch post after publishing."
    ],
    replies: [
      `Install and generate your first card:

pipx install termfetch
termfetch init --user YOUR_USERNAME --image photo.jpg
termfetch

Reply with your card. I’ll help the first 10 people configure theirs and repost my favorites.`,
      `Why a self-contained SVG?

Your README does not depend on an image server at view time. The card stays in a repository you control, and a scheduled GitHub Action can refresh the stats.`
    ]
  },
  {
    id: "themes",
    day: 2,
    title: "Theme gallery",
    scheduledAt: "2026-08-19T15:30:00.000Z",
    readiness: "ready",
    body: `Same GitHub profile, four terminal moods.

GitHub Dark, Dracula, Nord or GitHub Light—which one would you put in your README?

termfetch includes six themes and supports custom colors.

https://github.com/saivarun1410/termfetch`,
    media: {
      type: "image/png",
      url: "https://raw.githubusercontent.com/saivarun1410/termfetch/main/assets/theme-gallery.png",
      filename: "termfetch-theme-gallery.png"
    },
    notes: ["Reply to every choice with one useful customization tip."],
    replies: []
  },
  {
    id: "technical-story",
    day: 3,
    title: "Technical story",
    scheduledAt: "2026-08-20T15:30:00.000Z",
    readiness: "ready",
    body: `A GitHub README SVG cannot rely on a webfont.

termfetch positions every terminal glyph explicitly so ASCII columns do not drift when different operating systems choose different monospace fonts.

Small implementation detail. Much more reliable card.`,
    media: {
      type: "image/png",
      url: "https://raw.githubusercontent.com/saivarun1410/termfetch/main/assets/social-preview.png",
      filename: "termfetch-social-preview.png"
    },
    notes: [],
    replies: []
  },
  {
    id: "community-showcase",
    day: 4,
    title: "Community showcase",
    scheduledAt: "2026-08-21T15:30:00.000Z",
    readiness: "needs-edit",
    body: `The best part of releasing termfetch: seeing someone else’s profile become terminal art.

Here is [NAME]’s card in [THEME].

Want help making yours? Reply with your GitHub username.`,
    media: null,
    notes: [
      "Replace NAME and THEME before sharing.",
      "Get the creator’s permission and attach their card."
    ],
    replies: []
  },
  {
    id: "feature-poll",
    day: 5,
    title: "Feature poll",
    scheduledAt: "2026-08-22T15:30:00.000Z",
    readiness: "native-poll",
    body: `What should termfetch improve next?

1. More themes
2. Easier image cropping
3. More GitHub stats
4. A browser-based config preview`,
    media: null,
    notes: [
      "Use X’s poll button and enter the four choices.",
      "Turn the winning answer into a public GitHub issue."
    ],
    replies: []
  },
  {
    id: "before-after",
    day: 6,
    title: "Before and after",
    scheduledAt: "2026-08-23T15:30:00.000Z",
    readiness: "needs-media",
    body: `A profile README can be useful and still feel personal.

Before: a wall of badges.
After: one self-contained terminal card generated from your photo and GitHub data.

Built with termfetch: https://github.com/saivarun1410/termfetch`,
    media: null,
    notes: ["Attach honest before-and-after screenshots before sharing."],
    replies: []
  },
  {
    id: "week-one",
    day: 7,
    title: "Week-one recap",
    scheduledAt: "2026-08-24T15:30:00.000Z",
    readiness: "needs-edit",
    body: `One week since I released termfetch:

• [USERS] people tried it
• [CARDS] cards shared
• [STARS] GitHub stars
• [ISSUES] useful issues opened

Thank you to everyone who tested it. Next I’m working on [FEATURE].`,
    media: null,
    notes: ["Replace every bracketed value with the real number, even if it is small."],
    replies: []
  }
];

export function publicPosts() {
  return POSTS.map((post) => ({ ...post }));
}

export function duePosts(now = new Date(), windowHours = 12) {
  const cutoff = now.getTime() - windowHours * 60 * 60 * 1000;
  return POSTS.filter((post) => {
    const scheduled = Date.parse(post.scheduledAt);
    return scheduled <= now.getTime() && scheduled > cutoff;
  });
}

export function findPost(id) {
  return POSTS.find((post) => post.id === id) ?? null;
}
