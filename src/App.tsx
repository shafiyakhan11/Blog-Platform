import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import './App.css'

type CommentNode = {
  id: string
  author: string
  avatar: string
  content: string
  likes: number
  time: string
  replies: CommentNode[]
}

type Post = {
  id: string
  title: string
  excerpt: string
  content: string
  author: string
  authorHandle: string
  avatar: string
  tags: string[]
  publishedDate: string
  readTime: number
  likes: number
  views: number
  comments: CommentNode[]
  shares: number
  trendingScore: number
  isBookmarked: boolean
  isFollowed: boolean
}

const initialUser = {
  name: 'Your Name',
  username: '@yourname',
  email: 'you@example.com',
  followers: 1284,
  following: 248,
  bio: 'Writer, builder, and curious about the ideas that shape better products.',
}

const getUserInitials = (name: string) => {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length > 1) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return (parts[0] ?? 'U').slice(0, 2).toUpperCase()
}

const initialPosts: Post[] = [
  {
    id: 'post-1',
    title: 'Designing content systems that feel personal at scale',
    excerpt:
      'How teams can build editorial workflows that keep trust high while scaling dozens of voices without losing clarity.',
    content: `# Designing content systems that feel personal at scale

**Personalization** works when the system helps humans do the right thing, not when it replaces them.

- Create editorial guardrails.
- Measure signal over vanity metrics.
- Keep authors close to the reader journey.

> The goal is not more output. The goal is more clarity.

When you make the process visible and rewarding, readers feel the work before they even open the article.`,
    author: 'Ava Rodriguez',
    authorHandle: '@avawrites',
    avatar: 'AR',
    tags: ['Design', 'Strategy', 'Product'],
    publishedDate: 'July 18, 2026',
    readTime: 6,
    likes: 1248,
    views: 18400,
    comments: [
      {
        id: 'c1',
        author: 'Liam',
        avatar: 'L',
        content: 'The part about editorial guardrails is exactly what scaling teams miss.',
        likes: 42,
        time: '2h ago',
        replies: [
          {
            id: 'c1-1',
            author: 'Ava',
            avatar: 'AR',
            content: 'Thanks! Guardrails keep the producthuman regardless of volume.',
            likes: 12,
            time: '1h ago',
            replies: [],
          },
        ],
      },
      {
        id: 'c2',
        author: 'Nina',
        avatar: 'N',
        content: 'I would add author rituals to the system—review checklists matter more than fancy automation.',
        likes: 18,
        time: '34m ago',
        replies: [],
      },
    ],
    shares: 195,
    trendingScore: 980,
    isBookmarked: true,
    isFollowed: true,
  },
  {
    id: 'post-2',
    title: 'The future of AI-assisted writing is editorial, not mechanical',
    excerpt:
      'Writers are moving from “generate more text” to “design better judgment.” The best systems help editors win.',
    content: `# The future of AI-assisted writing is editorial, not mechanical

The shift is not from writing to automation. It is from word production to editorial judgment.

**Teams that win** use AI to:

1. Draft faster.
2. Surface missing angles.
3. Keep tone consistent.

The future belongs to people who understand context, taste, and trust.

Every article is a relationship between the writer, the reader, and the moment they are in.`,
    author: 'Milo Chen',
    authorHandle: '@milo',
    avatar: 'MC',
    tags: ['AI', 'Writing', 'Editorial'],
    publishedDate: 'July 15, 2026',
    readTime: 4,
    likes: 936,
    views: 14250,
    comments: [
      {
        id: 'c3',
        author: 'Priya',
        avatar: 'P',
        content: 'Exactly. The value is in the editorial layer.',
        likes: 33,
        time: '5h ago',
        replies: [],
      },
    ],
    shares: 120,
    trendingScore: 830,
    isBookmarked: false,
    isFollowed: false,
  },
  {
    id: 'post-3',
    title: 'How product teams build trust with release notes',
    excerpt:
      'Transparent release notes can reduce churn and help users understand the product story behind each iteration.',
    content: `# How product teams build trust with release notes

Trust is built less through launch hype and more through clear communication.

**Good release notes should teach**:

- what changed,
- why it changed,
- when to expect more changes.

A thoughtful update turns the product from an unknown system into a reliable partner.

The best documentation reads like a promise the team is willing to stand behind.`,
    author: 'Sofia ',
    authorHandle: '@sofiap',
    avatar: 'SP',
    tags: ['Product', 'UX', 'Communication'],
    publishedDate: 'July 10, 2026',
    readTime: 5,
    likes: 711,
    views: 9800,
    comments: [],
    shares: 88,
    trendingScore: 650,
    isBookmarked: true,
    isFollowed: true,
  },
  {
    id: 'post-4',
    title: 'Metrics that matter: a quieter dashboard for modern teams',
    excerpt:
      'A useful metrics story is not dense. It is honest, paced, and directly tied to the decisions teams actually make.',
    content: `# Metrics that matter: a quieter dashboard for modern teams

The best dashboard does not scream. It clarifies.

**A clearer dashboard answers**:

- are we learning,
- are we delivering,
- are we creating durable trust.

When your metrics resemble a story instead of a scoreboard, decision-making gets calmer and better.`,
    author: 'Jonah Reed',
    authorHandle: '@jonah',
    avatar: 'JR',
    tags: ['Analytics', 'Leadership', 'Product'],
    publishedDate: 'July 5, 2026',
    readTime: 7,
    likes: 680,
    views: 8700,
    comments: [],
    shares: 67,
    trendingScore: 600,
    isBookmarked: false,
    isFollowed: false,
  },
  
  {
    id: 'post-5',
    title: 'Practical RAG: Building AI Answers That Cite Their Sources',
    excerpt:
      'A grounded retrieval pipeline can make language model answers more useful, auditable, and easier to trust in production.',
    content: `# Practical RAG: Building AI Answers That Cite Their Sources

Retrieval augmented generation connects a language model to a carefully indexed knowledge base. The model first finds relevant passages, then uses those passages to draft an answer instead of relying only on its training memory.

Start with clean documents, meaningful chunk boundaries, and metadata that helps filter results. Evaluate retrieval and generation separately so you know whether a bad answer came from missing context or weak reasoning.`,
    author: 'Maya Patel',
    authorHandle: '@mayacodes',
    avatar: 'MP',
    tags: ['AI', 'Machine Learning', 'RAG'],
    publishedDate: 'August 18, 2026',
    readTime: 7,
    likes: 1420,
    views: 22100,
    comments: [],
    shares: 98,
    trendingScore: 980,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-6',
    title: 'Why Small Language Models Belong on the Edge',
    excerpt:
      'Smaller models can reduce latency, protect private data, and make intelligent features available without a constant cloud connection.',
    content: `# Why Small Language Models Belong on the Edge

Edge AI is not only about saving money. A model running near the user can respond quickly, continue working offline, and keep sensitive inputs inside a device or local network.

The best architecture assigns each task to the smallest model that can handle it. Use a local model for classification and suggestions, then reserve a larger hosted model for difficult requests that need broader context.`,
    author: 'Noah Williams',
    authorHandle: '@noahbuilds',
    avatar: 'NW',
    tags: ['AI', 'Edge Computing', 'Security'],
    publishedDate: 'August 15, 2026',
    readTime: 5,
    likes: 1180,
    views: 18700,
    comments: [],
    shares: 86,
    trendingScore: 860,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-7',
    title: 'The Computer Science of Better Recommendations',
    excerpt:
      'Recommendation systems become more helpful when they balance relevance, discovery, freshness, and the user control to change the outcome.',
    content: `# The Computer Science of Better Recommendations

A recommendation engine is an optimization system with a human experience attached to it. Historical clicks are useful signals, but they can also trap people in narrow patterns.

Combine collaborative signals with content features, freshness limits, and explicit feedback. Always measure more than engagement: useful recommendations should improve satisfaction and help users discover something they would not have found alone.`,
    author: 'Elena Garcia',
    authorHandle: '@elenadata',
    avatar: 'EG',
    tags: ['AI', 'Algorithms', 'Data Science'],
    publishedDate: 'August 12, 2026',
    readTime: 6,
    likes: 965,
    views: 15300,
    comments: [],
    shares: 74,
    trendingScore: 740,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-8',
    title: 'Zero Trust Networks for Growing IT Teams',
    excerpt:
      'Zero trust turns internal systems into protected boundaries by verifying every request instead of trusting a device because it sits on the office network.',
    content: `# Zero Trust Networks for Growing IT Teams

A zero trust program begins with identity, device posture, and least-privilege access. It does not require replacing every system at once.

Map the services people actually use, remove standing administrator access, and add short-lived permissions around sensitive actions. Logging each decision makes incidents easier to investigate and gives teams evidence that the controls are working.`,
    author: 'Marcus Lee',
    authorHandle: '@marcusinfra',
    avatar: 'ML',
    tags: ['IT', 'Cybersecurity', 'Networks'],
    publishedDate: 'August 9, 2026',
    readTime: 8,
    likes: 830,
    views: 12900,
    comments: [],
    shares: 68,
    trendingScore: 680,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-9',
    title: 'How Compilers Turn Human Ideas Into Machine Instructions',
    excerpt:
      'A compiler is a chain of transformations that preserves meaning while translating readable source code into efficient instructions.',
    content: `# How Compilers Turn Human Ideas Into Machine Instructions

The compiler pipeline usually moves through parsing, semantic analysis, an intermediate representation, optimization, and code generation. Each stage has a focused job and a clear contract with the next stage.

That separation is why compilers are such a useful computer science case study. They show how complex systems become manageable when each transformation can be inspected and tested independently.`,
    author: 'Owen Brooks',
    authorHandle: '@owencompiles',
    avatar: 'OB',
    tags: ['Computer Science', 'Compilers', 'Programming'],
    publishedDate: 'August 6, 2026',
    readTime: 9,
    likes: 790,
    views: 11600,
    comments: [],
    shares: 62,
    trendingScore: 620,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-10',
    title: 'Observability: The Missing Layer in Reliable Software',
    excerpt:
      'Logs explain events, metrics show trends, and traces connect a request across services so teams can debug systems from evidence.',
    content: `# Observability: The Missing Layer in Reliable Software

Monitoring tells you that something is wrong. Observability helps you ask better questions about why. A useful setup starts with a small set of service-level indicators tied to the experience users expect.

Add structured logs with request identifiers, traces across boundaries, and dashboards that show normal behavior as well as failure. The goal is not to collect everything; it is to make important paths understandable under pressure.`,
    author: 'Priya Shah',
    authorHandle: '@priyaships',
    avatar: 'PS',
    tags: ['IT', 'DevOps', 'SRE'],
    publishedDate: 'August 3, 2026',
    readTime: 6,
    likes: 720,
    views: 10400,
    comments: [],
    shares: 57,
    trendingScore: 570,
    isBookmarked: false,
    isFollowed: false,
  },
    {
    id: 'post-11',
    title: 'Designing APIs That Survive Their First Million Users',
    excerpt:
      'A stable API is a product contract: predictable resources, clear errors, safe retries, and versioning that respects existing clients.',
    content: `# Designing APIs That Survive Their First Million Users

Start with nouns and consistent representations before debating frameworks. Document required fields, pagination, rate limits, and error codes as part of the interface.

Idempotency keys make retryable writes safer, while compatibility tests prevent accidental breaking changes. Good API design reduces the number of special cases every client has to invent.`,
    author: 'Theo Martin',
    authorHandle: '@theobuilds',
    avatar: 'TM',
    tags: ['IT', 'APIs', 'Backend'],
    publishedDate: 'July 31, 2026',
    readTime: 7,
    likes: 680,
    views: 9800,
    comments: [],
    shares: 53,
    trendingScore: 530,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-12',
    title: 'A Gentle Introduction to Neural Network Training',
    excerpt:
      'Neural networks learn by adjusting parameters to reduce a measurable error, turning examples into a reusable function.',
    content: `# A Gentle Introduction to Neural Network Training

Training combines a forward pass, a loss calculation, backpropagation, and an optimizer update. The learning rate controls how aggressively parameters move, while the data determines what patterns the model can actually learn.

Validation data protects against confusing memorization with generalization. Small experiments with visible curves often teach more than changing ten hyperparameters at once.`,
    author: 'Aisha Johnson',
    authorHandle: '@aishaml',
    avatar: 'AJ',
    tags: ['AI', 'Deep Learning', 'Python'],
    publishedDate: 'July 28, 2026',
    readTime: 8,
    likes: 612,
    views: 9100,
    comments: [],
    shares: 49,
    trendingScore: 490,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-13',
    title: 'Database Indexes Explained Through Everyday Search',
    excerpt:
      'Indexes speed up reads by organizing lookup paths, but they add storage and write work that should match real query patterns.',
    content: `# Database Indexes Explained Through Everyday Search

Think of an index as a sorted guide that helps a database skip rows it does not need. A composite index can support several filters when its column order matches the way queries narrow results.

Indexes are not automatically good. Measure slow queries, inspect the query plan, and remove unused indexes that make writes more expensive without improving the product.`,
    author: 'Ravi Kumar',
    authorHandle: '@ravistack',
    avatar: 'RK',
    tags: ['Computer Science', 'Databases', 'Backend'],
    publishedDate: 'July 24, 2026',
    readTime: 6,
    likes: 590,
    views: 8700,
    comments: [],
    shares: 45,
    trendingScore: 450,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-14',
    title: 'The IT Playbook for a Calm Incident Response',
    excerpt:
      'Clear roles, short feedback loops, and practiced runbooks help teams solve outages without turning every incident into a blame exercise.',
    content: `# The IT Playbook for a Calm Incident Response

During an incident, one person should coordinate while others investigate, communicate, and make changes. A written timeline keeps facts separate from guesses and gives the team a shared operating picture.

After recovery, focus the review on system conditions and useful improvements. A good retrospective should produce fewer repeated failures, not just a longer document.`,
    author: 'Grace Kim',
    authorHandle: '@graceops',
    avatar: 'GK',
    tags: ['IT', 'Incident Response', 'Leadership'],
    publishedDate: 'July 20, 2026',
    readTime: 5,
    likes: 540,
    views: 7800,
    comments: [],
    shares: 41,
    trendingScore: 410,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-15',
    title: 'What Makes a Distributed System Distributed?',
    excerpt:
      'The hard part of distributed computing is not sending messages; it is reasoning about delay, partial failure, ordering, and consistency.',
    content: `# What Makes a Distributed System Distributed?

A local program can assume that memory is nearby and a response is either present or absent. A distributed system must handle requests that arrive late, twice, or not at all.

Designs become clearer when they state which guarantees matter. Choose consistency models, timeout behavior, and retry policies based on the domain instead of treating them as framework defaults.`,
    author: 'Daniel Okafor',
    authorHandle: '@danielsystems',
    avatar: 'DO',
    tags: ['Computer Science', 'Distributed Systems', 'Architecture'],
    publishedDate: 'July 17, 2026',
    readTime: 9,
    likes: 510,
    views: 7400,
    comments: [],
    shares: 38,
    trendingScore: 380,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-16',
    title: 'AI Evaluation Is an Engineering Discipline',
    excerpt:
      'A model demo is not a test suite. Reliable AI products need representative datasets, failure categories, and evaluation that runs continuously.',
    content: `# AI Evaluation Is an Engineering Discipline

Begin by writing down what a good answer means for the actual user. Build a small set of normal, ambiguous, adversarial, and out-of-scope examples.

Track quality by category rather than one blended score. Pair automated checks with human review for nuanced behavior, and keep evaluation data versioned so a model change can be explained rather than guessed at.`,
    author: 'Sofia Nguyen',
    authorHandle: '@sofiaevals',
    avatar: 'SN',
    tags: ['AI', 'Testing', 'Machine Learning'],
    publishedDate: 'July 13, 2026',
    readTime: 7,
    likes: 490,
    views: 7200,
    comments: [],
    shares: 35,
    trendingScore: 350,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-17',
    title: 'Operating Systems: Why Processes Need Boundaries',
    excerpt:
      'Processes give programs isolated memory and scheduling units, allowing one application to fail without bringing down the whole machine.',
    content: `# Operating Systems: Why Processes Need Boundaries

An operating system manages the tension between sharing and isolation. Processes share hardware through controlled system calls, virtual memory, and scheduling decisions made by the kernel.

Understanding those boundaries explains everyday behavior such as permissions, background work, and why a runaway program can consume resources without directly reading another program memory.`,
    author: 'Lucas Bennett',
    authorHandle: '@lucaskernel',
    avatar: 'LB',
    tags: ['Computer Science', 'Operating Systems', 'C'],
    publishedDate: 'July 9, 2026',
    readTime: 8,
    likes: 470,
    views: 6900,
    comments: [],
    shares: 33,
    trendingScore: 330,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-18',
    title: 'Cloud Cost Control Without Slowing Engineers Down',
    excerpt:
      'Visibility, budgets, and sensible defaults can lower cloud waste while keeping teams free to ship and experiment.',
    content: `# Cloud Cost Control Without Slowing Engineers Down

Cost control works best when it is close to the decision that creates the spend. Give each service an owner, show costs by environment, and alert on unusual changes rather than punishing every increase.

Automate easy wins such as idle resource cleanup and right-sizing. Treat performance, reliability, and cost as connected dimensions instead of asking teams to optimize one number in isolation.`,
    author: 'Hannah Wilson',
    authorHandle: '@hannahcloud',
    avatar: 'HW',
    tags: ['IT', 'Cloud', 'FinOps'],
    publishedDate: 'July 5, 2026',
    readTime: 6,
    likes: 445,
    views: 6500,
    comments: [],
    shares: 31,
    trendingScore: 310,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-19',
    title: 'The Hidden Mathematics Behind Public-Key Cryptography',
    excerpt:
      'Public-key cryptography uses problems that are easy to verify but difficult to reverse, enabling secure communication over an open network.',
    content: `# The Hidden Mathematics Behind Public-Key Cryptography

A key pair separates the ability to share a public value from the secret needed to prove ownership or decrypt information. In practice, protocols combine asymmetric cryptography with fast symmetric encryption for the data itself.

Security depends on implementation as much as mathematics. Key rotation, secure randomness, certificate validation, and careful libraries are essential parts of the system.`,
    author: 'Nadia Rahman',
    authorHandle: '@nadiasec',
    avatar: 'NR',
    tags: ['Computer Science', 'Security', 'Cryptography'],
    publishedDate: 'July 1, 2026',
    readTime: 8,
    likes: 420,
    views: 6100,
    comments: [],
    shares: 29,
    trendingScore: 290,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-20',
    title: 'Prompt Engineering Is Really Interface Design',
    excerpt:
      'A useful prompt gives an AI system context, constraints, and a clear output contract instead of relying on clever wording alone.',
    content: `# Prompt Engineering Is Really Interface Design

Treat a prompt like a small interface. Name the task, provide the relevant inputs, define what uncertainty should look like, and show the shape of the expected output.

Then test it with cases that expose ambiguity. Version prompts alongside code, measure failure patterns, and let the product decide when a human should review the result.`,
    author: 'Ethan Cole',
    authorHandle: '@ethanprompt',
    avatar: 'EC',
    tags: ['AI', 'Product', 'UX'],
    publishedDate: 'June 27, 2026',
    readTime: 5,
    likes: 405,
    views: 5900,
    comments: [],
    shares: 27,
    trendingScore: 270,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-21',
    title: 'Version Control Habits That Make Teams Faster',
    excerpt:
      'Good Git habits reduce coordination cost by making changes easy to review, revert, and understand months later.',
    content: `# Version Control Habits That Make Teams Faster

Small commits with specific messages create a useful history. Pull requests should explain intent and risk, not repeat every line of the diff.

Automated checks protect the main branch, while short-lived branches keep integration problems visible. The goal is not ceremony; it is a shared way to move changes safely through a team.`,
    author: 'Ivy Thompson',
    authorHandle: '@ivycodes',
    avatar: 'IT',
    tags: ['IT', 'Git', 'Engineering'],
    publishedDate: 'June 23, 2026',
    readTime: 5,
    likes: 390,
    views: 5700,
    comments: [],
    shares: 25,
    trendingScore: 250,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-22',
    title: 'Computer Vision Beyond Recognition',
    excerpt:
      'Modern vision systems can estimate depth, track motion, and understand scenes, but useful products still need context and careful boundaries.',
    content: `# Computer Vision Beyond Recognition

A camera model produces pixels; a vision system turns those pixels into decisions. Detection, segmentation, tracking, and classification solve different parts of that problem.

Accuracy should be measured across lighting, devices, people, and environments that resemble real use. Clear user feedback matters too, because no visual model is equally reliable in every situation.`,
    author: 'Mei Tan',
    authorHandle: '@meivision',
    avatar: 'MT',
    tags: ['AI', 'Computer Vision', 'Robotics'],
    publishedDate: 'June 19, 2026',
    readTime: 7,
    likes: 375,
    views: 5500,
    comments: [],
    shares: 23,
    trendingScore: 230,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-23',
    title: 'Why Data Structures Still Matter in the Age of AI',
    excerpt:
      'Efficient data structures shape the cost and clarity of every system, including the pipelines that train and serve modern AI models.',
    content: `# Why Data Structures Still Matter in the Age of AI

Arrays, trees, graphs, hash tables, and queues are not academic decorations. They determine how data is stored, searched, updated, and shared between components.

Choosing well means understanding the operations a product performs most often. A simpler structure with predictable behavior is frequently better than a clever one that nobody can maintain.`,
    author: 'Samir Das',
    authorHandle: '@samirlearns',
    avatar: 'SD',
    tags: ['Computer Science', 'Algorithms', 'Programming'],
    publishedDate: 'June 15, 2026',
    readTime: 6,
    likes: 360,
    views: 5200,
    comments: [],
    shares: 21,
    trendingScore: 210,
    isBookmarked: false,
    isFollowed: false,
  },

  {
    id: 'post-24',
    title: 'Building a Personal Lab for Learning Cloud Infrastructure',
    excerpt:
      'A small local lab can turn abstract infrastructure concepts into experiments you can observe, break, repair, and document.',
    content: `# Building a Personal Lab for Learning Cloud Infrastructure

Use containers or virtual machines to practice networking, service discovery, backups, and deployment workflows without needing a large budget. Keep each experiment small and write down what changed.

The most valuable result is not a perfect lab. It is the habit of forming a hypothesis, collecting evidence, and improving the system after it fails.`,
    author: 'Chloe Martin',
    authorHandle: '@chloelabs',
    avatar: 'CM',
    tags: ['IT', 'Cloud', 'Learning'],
    publishedDate: 'June 11, 2026',
    readTime: 5,
    likes: 340,
    views: 4900,
    comments: [],
    shares: 19,
    trendingScore: 190,
    isBookmarked: false,
    isFollowed: false,
  },

]



const defaultDraft = {
  title: '',
  excerpt: '',
  tags: 'Product,Design',
  content: '# New article\n\nWrite the story here...',
}

const parseMarkdown = (value: string) => {
  const escaped = value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  const withParagraphs = escaped
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n/g, '<br />')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^- (.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/> (.+)/g, '<blockquote>$1</blockquote>')
    .replace(/^# (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h4>$1</h4>')

  return `<p>${withParagraphs}</p>`
}

const addReplyToComments = (
  comments: CommentNode[],
  parentId: string,
  newComment: CommentNode,
): CommentNode[] =>
  comments.map((comment) => {
    if (comment.id === parentId) {
      return { ...comment, replies: [...comment.replies, newComment] }
    }

    return {
      ...comment,
      replies: addReplyToComments(comment.replies, parentId, newComment),
    }
  })

const addLikeToComment = (comments: CommentNode[], commentId: string): CommentNode[] =>
  comments.map((comment) => {
    if (comment.id === commentId) {
      return { ...comment, likes: comment.likes + 1 }
    }

    return {
      ...comment,
      replies: addLikeToComment(comment.replies, commentId),
    }
  })

const countComments = (comments: CommentNode[]): number =>
  comments.reduce(
    (total, comment) => total + 1 + countComments(comment.replies),
    0,
  )

function App() {
  const [authMode, setAuthMode] = useState<'login' | 'signup' | null>('login')
  const [authForm, setAuthForm] = useState({ name: '', email: '', password: '' })
  const [authError, setAuthError] = useState('')
  const [currentUser, setCurrentUser] = useState(initialUser)
  const [posts, setPosts] = useState<Post[]>(initialPosts)
  const [selectedTag, setSelectedTag] = useState('All')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [composerOpen, setComposerOpen] = useState(false)
  const [editingPostId, setEditingPostId] = useState<string | null>(null)
  const [draft, setDraft] = useState(defaultDraft)
  const [activePostId, setActivePostId] = useState(initialPosts[0].id)
  const [commentDrafts, setCommentDrafts] = useState<Record<string, string>>({})
  const [replyState, setReplyState] = useState<Record<string, string | null>>({})
  const [profileOpen, setProfileOpen] = useState(false)
  const [profileEditing, setProfileEditing] = useState(false)
  const [profileDraft, setProfileDraft] = useState(initialUser)
  const [showBackToTop, setShowBackToTop] = useState(false)
  const articleDetailRef = useRef<HTMLElement>(null)
  const commentComposerRef = useRef<HTMLDivElement>(null)
  const feedTopRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const updateBackToTopVisibility = () => {
      const composer = commentComposerRef.current
      const composerBounds = composer?.getBoundingClientRect()
      const postCommentIsVisible = composerBounds
        ? composerBounds.top < window.innerHeight && composerBounds.bottom > 0
        : false
      setShowBackToTop(postCommentIsVisible)
    }

    updateBackToTopVisibility()
    window.addEventListener('scroll', updateBackToTopVisibility, { passive: true })
    window.addEventListener('resize', updateBackToTopVisibility)

    return () => {
      window.removeEventListener('scroll', updateBackToTopVisibility)
      window.removeEventListener('resize', updateBackToTopVisibility)
    }
  }, [])

  const allTags = useMemo(
    () => ['All', ...Array.from(new Set(posts.flatMap((post) => post.tags)))],
    [posts],
  )

  const filteredPosts = useMemo(() => {
    return posts.filter((post) => {
      const matchesTag = selectedTag === 'All' || post.tags.includes(selectedTag)
      const haystack = `${post.title} ${post.excerpt} ${post.author} ${post.tags.join(' ')}`.toLowerCase()
      const matchesSearch = haystack.includes(searchTerm.toLowerCase())
      return matchesTag && matchesSearch
    })
  }, [posts, searchTerm, selectedTag])

  const pageSize = 3
  const totalPages = Math.max(1, Math.ceil(filteredPosts.length / pageSize))
  const visiblePosts = filteredPosts.slice((page - 1) * pageSize, page * pageSize)

  const activePost =
    posts.find((post) => post.id === activePostId) ?? filteredPosts[0] ?? posts[0]

  const trendingPosts = [...posts].sort((a, b) => b.trendingScore - a.trendingScore).slice(0, 4)
  const myPosts = posts.filter((post) => post.authorHandle === currentUser.username)
  const isOwnPost = activePost.authorHandle === currentUser.username

  const selectPost = (postId: string) => {
    setActivePostId(postId)
    requestAnimationFrame(() => {
      articleDetailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  const changePage = (nextPage: number) => {
    setPage(nextPage)
    requestAnimationFrame(() => {
      feedTopRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  const submitPost = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const normalizedTags = draft.tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)

    const content = draft.content.trim() || '# Untitled post\n\nAdd some writing here.'
    const timestamp = new Date().toISOString()

    if (editingPostId) {
      setPosts((currentPosts) =>
        currentPosts.map((post) =>
          post.id === editingPostId
            ? {
                ...post,
                title: draft.title.trim() || 'Untitled post',
                excerpt: draft.excerpt.trim() || 'A new editorial update.',
                tags: normalizedTags.length ? normalizedTags : ['Editorial'],
                content,
                readTime: Math.max(2, Math.round(content.split(/\s+/).length / 220)),
                publishedDate: new Date(timestamp).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                }),
              }
            : post,
        ),
      )
    } else {
      const newPost: Post = {
        id: `post-${Date.now()}`,
        title: draft.title.trim() || 'Untitled post',
        excerpt: draft.excerpt.trim() || 'A new editorial update.',
        content,
        author: currentUser.name,
        authorHandle: currentUser.username,
        avatar: getUserInitials(currentUser.name),
        tags: normalizedTags.length ? normalizedTags : ['Editorial'],
        publishedDate: new Date(timestamp).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        }),
        readTime: Math.max(2, Math.round(content.split(/\s+/).length / 220)),
        likes: 0,
        views: 0,
        comments: [],
        shares: 0,
        trendingScore: 0,
        isBookmarked: false,
        isFollowed: false,
      }

      setPosts((currentPosts) => [newPost, ...currentPosts])
      setActivePostId(newPost.id)
    }

    setComposerOpen(false)
    setEditingPostId(null)
    setDraft(defaultDraft)
  }

  const updateDraft = (field: keyof typeof defaultDraft, value: string) => {
    setDraft((current) => ({ ...current, [field]: value }))
  }

  const updateProfileDraft = (field: keyof typeof initialUser, value: string) => {
    setProfileDraft((current) => ({ ...current, [field]: value }))
  }

  const saveProfile = () => {
    setCurrentUser({ ...profileDraft })
    setProfileEditing(false)
  }

  const toggleLike = (postId: string) => {
    setPosts((currentPosts) =>
      currentPosts.map((post) =>
        post.id === postId ? { ...post, likes: post.likes + 1 } : post,
      ),
    )
  }

  const toggleBookmark = (postId: string) => {
    setPosts((currentPosts) =>
      currentPosts.map((post) =>
        post.id === postId ? { ...post, isBookmarked: !post.isBookmarked } : post,
      ),
    )
  }

  const toggleFollow = (postId: string) => {
    setPosts((currentPosts) =>
      currentPosts.map((post) =>
        post.id === postId ? { ...post, isFollowed: !post.isFollowed } : post,
      ),
    )
  }

  const handleShare = async (postId: string) => {
    const post = posts.find((item) => item.id === postId)
    if (!post) return

    const shareText = `Read "${post.title}" on PulseBlog — ${post.author}`

    try {
      await navigator.clipboard.writeText(shareText)
      setPosts((currentPosts) =>
        currentPosts.map((item) =>
          item.id === postId ? { ...item, shares: item.shares + 1 } : item,
        ),
      )
    } catch {
      setPosts((currentPosts) =>
        currentPosts.map((item) =>
          item.id === postId ? { ...item, shares: item.shares + 1 } : item,
        ),
      )
    }
  }

  const onCommentSubmit = (postId: string, parentId?: string) => {
    const key = parentId ?? postId
    const replyText = (commentDrafts[key] ?? '').trim()
    if (!replyText) return

    const newComment: CommentNode = {
      id: `comment-${Date.now()}`,
              author: currentUser.name,
              avatar: getUserInitials(currentUser.name),
      content: replyText,
      likes: 0,
      time: 'just now',
      replies: [],
    }

    setPosts((currentPosts) =>
      currentPosts.map((post) => {
        if (post.id !== postId) return post
        if (!parentId) {
          return { ...post, comments: [...post.comments, newComment] }
        }

        return {
          ...post,
          comments: addReplyToComments(post.comments, parentId, newComment),
        }
      }),
    )

    setCommentDrafts((current) => ({ ...current, [key]: '' }))
    setReplyState((current) => ({ ...current, [key]: null }))
  }

  const likeComment = (postId: string, commentId: string) => {
    setPosts((currentPosts) =>
      currentPosts.map((post) =>
        post.id === postId
          ? { ...post, comments: addLikeToComment(post.comments, commentId) }
          : post,
      ),
    )
  }

  const renderComment = (comment: CommentNode, depth = 0): React.ReactNode => (
    <div key={comment.id} className="comment-item" style={{ marginLeft: depth * 18 }}>
      <div className="comment-header">
        <div className="comment-avatar">{comment.avatar}</div>
        <div>
          <strong>{comment.author}</strong>
          <span>{comment.time}</span>
        </div>
      </div>
      <p>{comment.content}</p>
      <div className="comment-toolbar">
        <button type="button" onClick={() => likeComment(activePost.id, comment.id)}>
          ❤ {comment.likes}
        </button>
        <button type="button" onClick={() => setReplyState((current) => ({ ...current, [comment.id]: current[comment.id] ? null : comment.id }))}>
          Reply
        </button>
      </div>

      {replyState[comment.id] && (
        <div className="comment-reply-box">
          <textarea
            value={commentDrafts[comment.id] ?? ''}
            onChange={(event) =>
              setCommentDrafts((current) => ({
                ...current,
                [comment.id]: event.target.value,
              }))
            }
            placeholder="Write a reply..."
          />
          <button type="button" onClick={() => onCommentSubmit(activePost.id, comment.id)}>
            Add reply
          </button>
        </div>
      )}

      {comment.replies.map((reply) => renderComment(reply, depth + 1))}
    </div>
  )

  const editPost = (post: Post) => {
    setEditingPostId(post.id)
    setDraft({
      title: post.title,
      excerpt: post.excerpt,
      tags: post.tags.join(', '),
      content: post.content,
    })
    setComposerOpen(true)
  }

  const deletePost = (postId: string) => {
    setPosts((currentPosts) => currentPosts.filter((post) => post.id !== postId))
    if (activePostId === postId && posts.length > 1) {
      const remaining = posts.filter((post) => post.id !== postId)
      setActivePostId(remaining[0]?.id ?? '')
    }
  }

  const updateAuthForm = (field: keyof typeof authForm, value: string) => {
    setAuthForm((current) => ({ ...current, [field]: value }))
    setAuthError('')
  }

  const submitAuth = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!authForm.email.trim() || !authForm.password.trim() || (authMode === 'signup' && !authForm.name.trim())) {
      setAuthError('Please complete all required fields.')
      return
    }

    const name = authForm.name.trim() || authForm.email.split('@')[0]
    setCurrentUser((current) => ({
      ...current,
      name,
      username: `@${name.toLowerCase().replace(/[^a-z0-9]+/g, '') || 'writer'}`,
      email: authForm.email.trim(),
      followers: authMode === 'signup' ? 0 : current.followers,
      following: authMode === 'signup' ? 0 : current.following,
    }))
    setAuthMode(null)
  }

  const signInWithProvider = (provider: 'Google' | 'Facebook') => {
    const name = provider === 'Google' ? 'Google User' : 'Facebook User'
    const username = provider === 'Google' ? '@googleuser' : '@facebookuser'

    setCurrentUser((current) => ({
      ...current,
      name,
      username,
      email: `${provider.toLowerCase()}@example.com`,
    }))
    setAuthError('')
    setAuthMode(null)
  }

  const logout = () => {
    setProfileOpen(false)
    setProfileEditing(false)
    setAuthForm({ name: '', email: '', password: '' })
    setAuthError('')
    setAuthMode('login')
  }

  if (authMode !== null) {
    return (
      <main className="auth-page">
        <div className="auth-ambient auth-ambient--top" />
        <div className="auth-ambient auth-ambient--bottom" />
        <section className="auth-layout">
          <div className="auth-intro">
            <div className="auth-brand">
              <span className="brand-logo">P</span>
              <span>DraftFlow</span>
            </div>
            <div className="auth-intro-copy">
              <span className="auth-kicker">A home for good ideas</span>
              <h1>Draft your thoughts. Flow with the world.</h1>
              <p>Publish thoughtful work, find your people, and build a body of ideas worth returning to.</p>
            </div>
            <div className="auth-quote">
              <span className="quote-mark">“</span>
              <p>DraftFlow gives my thinking a place to breathe. The right readers always seem to find it.</p>
              <div className="quote-author"><span className="quote-avatar">AR</span><span><strong>Ava Rodriguez</strong><small>Writer & editor</small></span></div>
            </div>
          </div>

          <section className="auth-card">
            <div className="auth-card-header">
              <span className="auth-card-label">{authMode === 'login' ? 'Welcome back' : 'Start writing'}</span>
              <h2>{authMode === 'login' ? 'Sign in to DraftFlow' : 'Create your account'}</h2>
              <p>{authMode === 'login' ? 'Pick up where your ideas left off.' : 'Your next great story starts with a blank page.'}</p>
            </div>

            <div className="auth-tabs" role="tablist" aria-label="Authentication options">
              <button type="button" className={authMode === 'login' ? 'active' : ''} onClick={() => setAuthMode('login')}>Sign in</button>
              <button type="button" className={authMode === 'signup' ? 'active' : ''} onClick={() => setAuthMode('signup')}>Sign up</button>
            </div>

            <form className="auth-form" onSubmit={submitAuth}>
              {authMode === 'signup' && (
                <label><span>Your name</span><input autoFocus value={authForm.name} onChange={(event) => updateAuthForm('name', event.target.value)} placeholder="Ava Rodriguez" /></label>
              )}
              <label><span>Email address</span><input type="email" value={authForm.email} onChange={(event) => updateAuthForm('email', event.target.value)} placeholder="you@example.com" /></label>
              <label><span>Password</span><input type="password" value={authForm.password} onChange={(event) => updateAuthForm('password', event.target.value)} placeholder="••••••••" /></label>
              <div className="auth-form-meta">
                <label className="check-label"><input type="checkbox" /> <span>Remember me</span></label>
                {authMode === 'login' && <button type="button" className="auth-link">Forgot password?</button>}
              </div>
              {authError && <p className="auth-error" role="alert">{authError}</p>}
              <button type="submit" className="auth-submit">{authMode === 'login' ? 'Sign in' : 'Create account'} <span>→</span></button>
            </form>

            <div className="auth-divider"><span>or continue with</span></div>
            <div className="social-buttons">
              <button type="button" className="social-button" onClick={() => signInWithProvider('Google')}>
                <span className="google-mark">G</span>
                Continue with Google
              </button>
              <button type="button" className="social-button" onClick={() => signInWithProvider('Facebook')}>
                <span className="facebook-mark">f</span>
                Continue with Facebook
              </button>
            </div>
            <p className="auth-switch">{authMode === 'login' ? 'New to DraftFlow?' : 'Already have an account?'} <button type="button" className="auth-link" onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>{authMode === 'login' ? 'Create an account' : 'Sign in'}</button></p>
          </section>
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-logo">P</div>
          <div>
            <p className="eyebrow">Your Own Workspace</p>
            <h1>DraftFlow</h1>
          </div>
        </div>

        <label className="search-box" aria-label="Search posts">
          <span>⌕</span>
          <input
            type="search"
            value={searchTerm}
            onChange={(event) => {
              setSearchTerm(event.target.value)
              setPage(1)
            }}
            placeholder="Search articles, authors, tags"
          />
        </label>

        <div className="topbar-actions">
          <button type="button" className="profile-trigger" onClick={() => setProfileOpen(true)}>
            <span className="author-avatar">{getUserInitials(currentUser.name)}</span>
            <span>{currentUser.name}</span>
          </button>
          <button type="button" className="primary-button" onClick={() => setComposerOpen(true)}>
            + New post
          </button>
        </div>
      </header>

      {profileOpen && (
        <section className="user-profile-page">
          <div className="profile-page-header">
            <div>
              <span className="pill">Your profile</span>
              <h2>Profile & account</h2>
              <p>Manage the public details and community activity for your DraftFlow account.</p>
            </div>
            <div className="profile-page-actions">
              <button
                type="button"
                className="profile-back-button"
                onClick={() => {
                  setProfileEditing(false)
                  setProfileOpen(false)
                }}
              >
                ← Back to feed
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => {
                  setProfileDraft(currentUser)
                  setProfileEditing(true)
                }}
              >
                Edit profile
              </button>
              <button type="button" className="logout-button" onClick={logout}>
                Log out
              </button>
            </div>
          </div>

          <div className="profile-page-grid">
            <section className="profile-identity-card">
              <div className="profile-page-avatar">{getUserInitials(currentUser.name)}</div>
              {profileEditing ? (
                <div className="profile-edit-form">
                  <label>
                    Name
                    <input value={profileDraft.name} onChange={(event) => updateProfileDraft('name', event.target.value)} />
                  </label>
                  <label>
                    Username
                    <input value={profileDraft.username} onChange={(event) => updateProfileDraft('username', event.target.value)} />
                  </label>
                  <label>
                    Email address
                    <input type="email" value={profileDraft.email} onChange={(event) => updateProfileDraft('email', event.target.value)} />
                  </label>
                  <label>
                    Bio
                    <textarea value={profileDraft.bio} onChange={(event) => updateProfileDraft('bio', event.target.value)} rows={3} />
                  </label>
                  <div className="profile-edit-actions">
                    <button type="button" className="secondary-button" onClick={() => setProfileEditing(false)}>Cancel</button>
                    <button type="button" className="primary-button" onClick={saveProfile}>Save profile</button>
                  </div>
                </div>
              ) : (
                <>
                  <h3>{currentUser.name}</h3>
                  <p className="profile-username">{currentUser.username}</p>
                  <p className="profile-bio">{currentUser.bio}</p>
                  <div className="profile-email">
                    <span>Email address</span>
                    <strong>{currentUser.email}</strong>
                  </div>
                </>
              )}
            </section>

            <section className="profile-details-card">
              <div className="section-head">
                <p>Community overview</p>
                <span>Active member</span>
              </div>
              <div className="profile-page-stats">
                <div>
                  <strong>{currentUser.followers.toLocaleString()}</strong>
                  <span>Followers</span>
                </div>
                <div>
                  <strong>{currentUser.following.toLocaleString()}</strong>
                  <span>Following</span>
                </div>
                <div>
                  <strong>{myPosts.length}</strong>
                  <span>Published posts</span>
                </div>
              </div>
              <div className="profile-detail-list">
                <div>
                  <span>Profile visibility</span>
                  <strong>Public</strong>
                </div>
                <div>
                  <span>Member since</span>
                  <strong>August 2026</strong>
                </div>
              </div>
            </section>
          </div>

          <section className="my-blogs-section">
            <div className="section-head">
              <p>My posts</p>
              <span>{myPosts.length} published</span>
            </div>
            {myPosts.length === 0 ? (
              <button type="button" className="add-first-blog" onClick={() => setComposerOpen(true)}>
                + Add your first post
              </button>
            ) : (
              <div className="my-blogs-list">
                {myPosts.map((post) => (
                  <button type="button" key={post.id} onClick={() => {
                    setProfileOpen(false)
                    selectPost(post.id)
                  }}>
                    <strong>{post.title}</strong>
                    <span>{post.publishedDate} · {post.readTime} min read</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </section>
      )}

      <main className={profileOpen ? 'layout-grid is-hidden' : 'layout-grid'}>
        <aside className="sidebar left-panel">
          <section className="panel-card panel-card--soft">
            <div className="section-head">
              <p>Trending now</p>
              <span>live</span>
            </div>
            <ul className="trending-list">
              {trendingPosts.map((post, index) => (
                <li key={post.id} onClick={() => selectPost(post.id)}>
                  <span className="rank">0{index + 1}</span>
                  <div>
                    <h3>{post.title}</h3>
                    <small>
                      {post.likes} likes • {countComments(post.comments)} comments
                    </small>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="panel-card">
            <div className="section-head">
              <p>Topics</p>
            </div>
            <div className="tag-cloud">
              {allTags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  className={tag === selectedTag ? 'tag active' : 'tag'}
                  onClick={() => {
                    setSelectedTag(tag)
                    setPage(1)
                  }}
                >
                  #{tag}
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="content-column">
          <div ref={feedTopRef} className="featured-card">
            <div className="featured-copy">
              <span className="pill">Featured</span>
              <h2>{activePost.title}</h2>
              <p>{activePost.excerpt}</p>
              <div className="meta-row">
                <span>{activePost.author}</span>
                <span>{activePost.publishedDate}</span>
                <span>{activePost.readTime} min read</span>
              </div>
            </div>
            <div className="featured-metrics">
              <div>
                <strong>{activePost.likes}</strong>
                <span>likes</span>
              </div>
              <div>
                <strong>{countComments(activePost.comments)}</strong>
                <span>comments</span>
              </div>
              <div>
                <strong>{activePost.shares}</strong>
                <span>shares</span>
              </div>
            </div>
          </div>

          <div key={page} className="feed-list page-transition">
            {visiblePosts.map((post) => (
              <article
                key={post.id}
                className={post.id === activePost.id ? 'post-card active' : 'post-card'}
                onClick={() => selectPost(post.id)}
              >
                <div className="post-header">
                  <div className="author-block">
                    <div className="author-avatar">{post.avatar}</div>
                    <div>
                      <h3>{post.author}</h3>
                      <small>{post.authorHandle}</small>
                    </div>
                  </div>
                  <div className="status-badges">
                    <span>{post.readTime} min</span>
                    <span>{post.tags[0]}</span>
                  </div>
                </div>

                <h2>{post.title}</h2>
                <p>{post.excerpt}</p>

                <div className="tag-row">
                  {post.tags.map((tag) => (
                    <button key={tag} type="button" className="tag mini" onClick={(event) => {
                      event.stopPropagation()
                      setSelectedTag(tag)
                    }}>
                      #{tag}
                    </button>
                  ))}
                </div>

                <div className="post-footer">
                  <div className="stat-row">
                    <span>❤ {post.likes}</span>
                    <span>💬 {countComments(post.comments)}</span>
                    <span>👁 {post.views}</span>
                  </div>

                  <div className="action-row">
                    <button type="button" onClick={(event) => {
                      event.stopPropagation()
                      toggleLike(post.id)
                    }}>
                      Like
                    </button>
                    <button type="button" onClick={(event) => {
                      event.stopPropagation()
                      toggleBookmark(post.id)
                    }}>
                      {post.isBookmarked ? 'Saved' : 'Save'}
                    </button>
                    <button type="button" onClick={(event) => {
                      event.stopPropagation()
                      handleShare(post.id)
                    }}>
                      Share
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>

          <div className="pagination">
            <button type="button" disabled={page === 1} onClick={() => changePage(page - 1)}>
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button type="button" disabled={page === totalPages} onClick={() => changePage(page + 1)}>
              Next
            </button>
          </div>
        </section>

        <aside className="sidebar right-panel">
          <section className="panel-card">
            <div className="section-head">
              <p>Author profile</p>
              <button type="button" className="text-button" onClick={() => toggleFollow(activePost.id)}>
                {activePost.isFollowed ? 'Following' : 'Follow author'}
              </button>
            </div>

            <div className="author-profile">
              <div className="large-avatar">{activePost.avatar}</div>
              <div>
                <h3>{activePost.author}</h3>
                <p>{activePost.authorHandle}</p>
              </div>
            </div>

            <div className="profile-stats">
              <div>
                <strong>{activePost.views.toLocaleString()}</strong>
                <span>reads</span>
              </div>
              <div>
                <strong>{activePost.likes}</strong>
                <span>likes</span>
              </div>
              <div>
                <strong>{countComments(activePost.comments)}</strong>
                <span>comments</span>
              </div>
            </div>
          </section>

          <section className="panel-card">
            <div className="section-head">
              <p>SEO snapshot</p>
            </div>
            <ul className="seo-list">
              <li>
                <span>Score</span>
                <strong>98/100</strong>
              </li>
              <li>
                <span>Meta title</span>
                <strong>{activePost.title.slice(0, 42)}...</strong>
              </li>
              <li>
                <span>Keywords</span>
                <strong>{activePost.tags.join(', ')}</strong>
              </li>
            </ul>
          </section>

          <section className="panel-card">
            <div className="section-head">
              <p>Bookmarks</p>
            </div>
            <ul className="bookmark-list">
              {posts.filter((post) => post.isBookmarked).map((post) => (
                <li key={post.id}>
                  <button type="button" onClick={() => selectPost(post.id)}>{post.title}</button>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </main>

      <section
        ref={articleDetailRef}
        className={profileOpen ? 'article-detail is-hidden' : 'article-detail'}
      >
        <div className="article-meta-row">
          <div>
            <span className="pill neutral">Article</span>
            <h2>{activePost.title}</h2>
          </div>
          {isOwnPost && (
            <div className="article-actions">
              <button type="button" onClick={() => editPost(activePost)}>Edit</button>
              <button type="button" className="danger" onClick={() => deletePost(activePost.id)}>
                Delete
              </button>
            </div>
          )}
        </div>

        <div className="article-header-row">
          <div className="author-block">
            <div className="author-avatar">{activePost.avatar}</div>
            <div>
              <h3>{activePost.author}</h3>
              <small>
                {activePost.publishedDate} • {activePost.readTime} min read
              </small>
            </div>
          </div>
          <div className="article-toolbar">
            <button type="button" onClick={() => toggleLike(activePost.id)}>❤ {activePost.likes}</button>
            <button type="button" onClick={() => toggleBookmark(activePost.id)}>
              {activePost.isBookmarked ? 'Bookmarked' : 'Bookmark'}
            </button>
            <button type="button" onClick={() => handleShare(activePost.id)}>Share</button>
          </div>
        </div>

        <div className="article-body" dangerouslySetInnerHTML={{ __html: parseMarkdown(activePost.content) }} />

        <div className="comment-box">
          <div className="section-head">
            <p>Comments</p>
            <span>{countComments(activePost.comments)} total</span>
          </div>

          <div ref={commentComposerRef} className="comment-composer">
            <textarea
              value={commentDrafts[activePost.id] ?? ''}
              onChange={(event) =>
                setCommentDrafts((current) => ({
                  ...current,
                  [activePost.id]: event.target.value,
                }))
              }
              placeholder="Share your thoughts..."
            />
            <button type="button" onClick={() => onCommentSubmit(activePost.id)}>
              Post comment
            </button>
          </div>

          <div className="comment-tree">{activePost.comments.map((comment) => renderComment(comment))}</div>
        </div>
      </section>

      {showBackToTop && (
        <button
          type="button"
          className="back-to-top"
          aria-label="Back to top"
          title="Back to top"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          ↑
        </button>
      )}

      {composerOpen && (
        <div className="modal-backdrop" onClick={() => setComposerOpen(false)}>
          <div className="editor-modal" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingPostId ? 'Edit post' : 'Create post'}</h3>
              <button type="button" onClick={() => setComposerOpen(false)}>Close</button>
            </div>

            <form onSubmit={submitPost} className="composer-form">
              <div className="form-row split">
                <label>
                  <span>Title</span>
                  <input
                    value={draft.title}
                    onChange={(event) => updateDraft('title', event.target.value)}
                    placeholder="Your headline"
                  />
                </label>
                <label>
                  <span>Tags</span>
                  <input
                    value={draft.tags}
                    onChange={(event) => updateDraft('tags', event.target.value)}
                    placeholder="Product, Growth, Design"
                  />
                </label>
              </div>

              <label>
                <span>Excerpt</span>
                <textarea
                  value={draft.excerpt}
                  onChange={(event) => updateDraft('excerpt', event.target.value)}
                  rows={3}
                  placeholder="A short summary for your readers"
                />
              </label>

              <div className="editor-toolbar">
                <button type="button" onClick={() => updateDraft('content', `${draft.content}\n**Bold**`)}>
                  Bold
                </button>
                <button type="button" onClick={() => updateDraft('content', `${draft.content}\n*Italic*`)}>
                  Italic
                </button>
                <button type="button" onClick={() => updateDraft('content', `${draft.content}\n- list item`)}>
                  List
                </button>
                <button type="button" onClick={() => updateDraft('content', `${draft.content}\n> quote`)}>
                  Quote
                </button>
              </div>

              <label>
                <span>Story</span>
                <textarea
                  value={draft.content}
                  onChange={(event) => updateDraft('content', event.target.value)}
                  rows={10}
                  placeholder="Write your article in markdown"
                />
              </label>

              <div className="preview-box" dangerouslySetInnerHTML={{ __html: parseMarkdown(draft.content) }} />

              <div className="form-actions">
                <button type="button" className="secondary-button" onClick={() => setComposerOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={!draft.content.trim()}>
                  {editingPostId ? 'Save changes' : 'Publish article'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
