// Sample data so the UI can be previewed without Postgres, Redis or an API key.
// `npm run demo`. Nothing in here touches the network.
import type { AnswerResult, ChatReply, Course, Doc, Progress, Question, QueueStats } from './types'

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))

const CANNED: { match: RegExp; reply: Omit<ChatReply, 'conversation_id'> }[] = [
  {
    match: /dijkstra|negative/i,
    reply: {
      parts: [
        { text: 'Dijkstra finalises a vertex the moment it comes off the priority queue, and it never looks at that vertex again.', refs: [1] },
        { text: ' The correctness proof leans on one assumption: once u is extracted, no later path can be shorter than d[u], because every extra edge only adds weight.', refs: [1] },
        { text: ' A negative edge breaks that. A path found later can go through it and end up cheaper than the distance already locked in, but the algorithm has no step that revisits u.', refs: [1, 2] },
        { text: '\n\nSmall example: s→a costs 2, s→b costs 5, b→a costs −4. Dijkstra pops a with d[a] = 2 and is done with it, while the real shortest distance is 1 via b.', refs: [2] },
        { text: ' For graphs with negative weights (and no negative cycle) use Bellman-Ford, O(VE).', refs: [3] },
        { text: '\n\nCommon mistake on exams: saying "Dijkstra loops forever". It doesn\'t, it terminates and just returns a wrong answer.', refs: [] },
      ],
      sources: [
        { n: 1, source: 'demo/lec14-shortest-paths.pdf#page=22', title: 'DAA · lec14-shortest-paths.pdf · p.22', quote: 'Invariant: when u is extracted from Q, d[u] = δ(s,u). Proof relies on w(e) ≥ 0 for all e: any path leaving S has weight at least d[u].' },
        { n: 2, source: 'demo/lec14-shortest-paths.pdf#page=24', title: 'DAA · lec14-shortest-paths.pdf · p.24', quote: 'Counterexample with a negative edge: a is finalised at distance 2, but s→b→a has weight 1.' },
        { n: 3, source: 'demo/clrs-ch24.pdf#page=7', title: 'DAA · clrs-ch24.pdf · p.7', quote: 'The Bellman-Ford algorithm solves the single-source shortest-paths problem in the general case in which edge weights may be negative.' },
      ],
    },
  },
  {
    match: /alpha|beta|minimax|pruning/i,
    reply: {
      parts: [
        { text: 'With perfect move ordering alpha-beta examines O(b^(m/2)) nodes instead of minimax\'s O(b^m).', refs: [1] },
        { text: ' Put differently, in the same time you can search about twice as deep.', refs: [1] },
        { text: ' With random ordering it\'s roughly O(b^(3m/4)).', refs: [2] },
        { text: '\n\nPruning never changes the value at the root, only how much of the tree you look at. That\'s a favourite true/false question.', refs: [2] },
      ],
      sources: [
        { n: 1, source: 'demo/ai-lec06-adversarial-search.pdf#page=31', title: 'AI · ai-lec06-adversarial-search.pdf · p.31', quote: 'With perfect ordering, time complexity drops to O(b^{m/2}): effective branching factor √b, doubling the solvable depth.' },
        { n: 2, source: 'demo/ai-lec06-adversarial-search.pdf#page=29', title: 'AI · ai-lec06-adversarial-search.pdf · p.29', quote: 'Pruning does not affect the final result. Good move ordering improves the effectiveness of pruning.' },
      ],
    },
  },
  {
    match: /observer|pattern/i,
    reply: {
      parts: [
        { text: 'Observer defines a one-to-many dependency: when the subject changes state, every registered observer gets notified and updates itself.', refs: [1] },
        { text: ' The subject only knows the Observer interface, not the concrete classes, which is the loose coupling the lecture keeps coming back to.', refs: [1, 2] },
        { text: '\n\nIn the sequence diagram the subject calls notify(), which loops over observers calling update().', refs: [2] },
      ],
      sources: [
        { n: 1, source: 'demo/swe-lec09-patterns.pdf#page=14', title: 'SWE · swe-lec09-patterns.pdf · p.14', quote: 'Observer: define a one-to-many dependency between objects so that when one object changes state, all its dependents are notified.' },
        { n: 2, source: 'demo/swe-lec09-patterns.pdf#page=16', title: 'SWE · swe-lec09-patterns.pdf · p.16', quote: 'Subject is coupled only to the abstract Observer interface.' },
      ],
    },
  },
  {
    match: /weak|study|focus|how am i/i,
    reply: {
      parts: [
        { text: 'Based on your quiz history, the three to put time into first:\n\n1. Dynamic programming (DAA), mastery 0.31 over 9 attempts. You keep losing points on writing the recurrence before the table.\n2. MDPs and reinforcement learning (AI), 0.38. Mostly mixing up value iteration and policy iteration.\n3. Design patterns (SWE), 0.45, and SWE is the first exam (Dec 16).\n\nNetwork flow hasn\'t been tested yet, so the quiz will start pulling it in soon.', refs: [] },
      ],
      sources: [],
    },
  },
]

const NOT_COVERED: Omit<ChatReply, 'conversation_id'> = {
  parts: [
    { text: 'I searched the slides, the textbook chapters and your notes twice and couldn\'t find this, so it doesn\'t look like it\'s in the course material.', refs: [] },
    { text: '\n\nNot from the course: in general terms, this is outside what the three exams cover, so I\'d skip it for now.', refs: [] },
  ],
  sources: [],
}

const QUESTIONS: Record<Course, (Question & { _answer: string; _expl: string })[]> = {
  daa: [
    {
      id: 'q-daa-1', topic_id: 'daa.dp', topic_name: 'Dynamic programming', kind: 'mcq',
      question: 'For 0/1 knapsack with n items and capacity W, why is the O(nW) DP not a polynomial-time algorithm?',
      choices: [
        'Because the table has n·W cells and W can be exponential in the input size',
        'Because each cell takes O(n) time to fill',
        'Because knapsack has no optimal substructure',
        'Because the DP has to try all 2^n subsets',
      ],
      reason: 'practice', reason_text: 'Practice: dynamic programming is your weakest DAA topic',
      _answer: 'Because the table has n·W cells and W can be exponential in the input size',
      _expl: 'W is written in log W bits, so O(nW) is pseudo-polynomial: polynomial in the value of W, exponential in its length.',
    },
    {
      id: 'q-daa-2', topic_id: 'daa.shortest_paths', topic_name: 'Shortest paths', kind: 'short',
      question: 'Explain why Dijkstra\'s algorithm can return a wrong answer when the graph has a negative edge weight.',
      choices: [], reason: 'review', reason_text: 'Review: you missed this 3 days ago',
      _answer: 'Dijkstra finalises a vertex when it\'s extracted from the priority queue. A negative edge found later could lower that vertex\'s distance, but it is never revisited.',
      _expl: '',
    },
  ],
  swe: [
    {
      id: 'q-swe-1', topic_id: 'swe.patterns', topic_name: 'Design patterns', kind: 'mcq',
      question: 'Which pattern lets you add responsibilities to an object at runtime without subclassing?',
      choices: ['Decorator', 'Adapter', 'Template Method', 'Singleton'],
      reason: 'practice', reason_text: 'Practice: design patterns, and SWE is your first exam',
      _answer: 'Decorator',
      _expl: 'Decorator wraps an object behind the same interface and adds behaviour before/after delegating. Adapter changes the interface; Template Method uses inheritance.',
    },
  ],
  ai: [
    {
      id: 'q-ai-1', topic_id: 'ai.mdp_rl', topic_name: 'MDPs and reinforcement learning', kind: 'short',
      question: 'What is the difference between value iteration and policy iteration?',
      choices: [], reason: 'practice', reason_text: 'Practice: MDPs and RL needs work',
      _answer: 'Value iteration repeatedly applies the Bellman optimality update to V until it converges, then extracts a policy. Policy iteration alternates full policy evaluation of a fixed policy with greedy policy improvement, and stops when the policy stops changing.',
      _expl: '',
    },
  ],
}

let qIndex: Record<Course, number> = { daa: 0, swe: 0, ai: 0 }

const docs: Doc[] = [
  { id: 'd1', filename: 'lec14-shortest-paths.pdf', course_id: 'daa', status: 'done', pages: 38, chunks: 41, error: null },
  { id: 'd2', filename: 'clrs-ch24.pdf', course_id: 'daa', status: 'done', pages: 31, chunks: 87, error: null },
  { id: 'd3', filename: 'lec11-dynamic-programming.pdf', course_id: 'daa', status: 'done', pages: 44, chunks: 52, error: null },
  { id: 'd4', filename: 'DAA-Final-Study-Plan.md', course_id: 'daa', status: 'done', pages: 12, chunks: 19, error: null },
  { id: 'd5', filename: 'swe-lec09-patterns.pdf', course_id: 'swe', status: 'done', pages: 52, chunks: 58, error: null },
  { id: 'd6', filename: 'swe-lec12-testing.pdf', course_id: 'swe', status: 'processing', pages: null, chunks: 0, error: null },
  { id: 'd7', filename: 'study-schedule.md', course_id: 'swe', status: 'done', pages: 6, chunks: 9, error: null },
  { id: 'd8', filename: 'ai-lec06-adversarial-search.pdf', course_id: 'ai', status: 'done', pages: 47, chunks: 50, error: null },
  { id: 'd9', filename: 'ai-lec10-mdps.pdf', course_id: 'ai', status: 'queued', pages: null, chunks: 0, error: null },
  { id: 'd10', filename: 'ai-practice-final-2024-scan.pdf', course_id: 'ai', status: 'failed', pages: 9, chunks: 0, error: 'no text extracted (9 pages), looks scanned' },
]

const queue: QueueStats = { pending: 1, delayed: 0, dead: 1, workers: 3 }

function day(offset: number) {
  const d = new Date()
  d.setDate(d.getDate() - offset)
  return d.toISOString().slice(0, 10)
}

const progress: Progress = {
  weakest: [
    { id: 'daa.dp', name: 'Dynamic programming', course_id: 'daa', attempts: 9, mastery: 0.31, priority: 1.04 },
    { id: 'ai.mdp_rl', name: 'MDPs and reinforcement learning', course_id: 'ai', attempts: 6, mastery: 0.38, priority: 0.87 },
    { id: 'daa.flow', name: 'Network flow and matching', course_id: 'daa', attempts: 0, mastery: 0, priority: 1.2 },
    { id: 'swe.patterns', name: 'Design patterns', course_id: 'swe', attempts: 11, mastery: 0.45, priority: 0.77 },
    { id: 'daa.np', name: 'NP-completeness and reductions', course_id: 'daa', attempts: 4, mastery: 0.5, priority: 0.65 },
  ].sort((a, b) => b.priority - a.priority) as Progress['weakest'],
  mastery: [
    ['daa.asymptotics', 'Asymptotics', 'daa', 0.86], ['daa.divide_conquer', 'Divide & conquer', 'daa', 0.74],
    ['daa.greedy', 'Greedy', 'daa', 0.62], ['daa.dp', 'Dynamic prog.', 'daa', 0.31],
    ['daa.graphs_basic', 'BFS / DFS / SCC', 'daa', 0.81], ['daa.shortest_paths', 'Shortest paths', 'daa', 0.58],
    ['daa.mst', 'MST', 'daa', 0.77], ['daa.flow', 'Network flow', 'daa', 0], ['daa.np', 'NP-completeness', 'daa', 0.5],
    ['swe.process', 'Process models', 'swe', 0.9], ['swe.requirements', 'Requirements', 'swe', 0.72],
    ['swe.uml', 'UML', 'swe', 0.66], ['swe.design', 'SOLID', 'swe', 0.7], ['swe.patterns', 'Patterns', 'swe', 0.45],
    ['swe.testing', 'Testing', 'swe', 0.63], ['swe.vcs_ci', 'CI/CD', 'swe', 0.88],
    ['ai.search', 'Search / A*', 'ai', 0.79], ['ai.adversarial', 'Minimax / α-β', 'ai', 0.69],
    ['ai.csp', 'CSP', 'ai', 0.6], ['ai.logic', 'Logic', 'ai', 0.55], ['ai.probability', 'Bayes nets', 'ai', 0.52],
    ['ai.mdp_rl', 'MDPs / RL', 'ai', 0.38], ['ai.ml', 'Supervised', 'ai', 0.74],
  ].map(([id, name, course_id, mastery]) => ({
    id, name, course_id, mastery, attempts: 5, priority: 0,
  })) as Progress['mastery'],
  daily: [
    0, 0.52, 0.48, null, 0.55, 0.61, 0.58, 0.64, null, 0.6, 0.67, 0.7, 0.66, 0.74,
  ].map((accuracy, i) => ({
    day: day(13 - i),
    answered: accuracy === null ? 0 : 8 + ((i * 7) % 13),
    accuracy: accuracy === 0 ? null : (accuracy as number | null),
  })),
  spend: [
    { kind: 'chat', calls: 64, usd: 2.4312, avg_ms: 6120, cache_hit: 0.71 },
    { kind: 'quiz_gen', calls: 14, usd: 0.8455, avg_ms: 18400, cache_hit: 0 },
    { kind: 'grade', calls: 37, usd: 0.5180, avg_ms: 4300, cache_hit: 0 },
    { kind: 'label', calls: 600, usd: 3.5520, avg_ms: 1900, cache_hit: 0 },
  ],
  queue,
}

export const api = {
  async chat(message: string, conversation_id?: string): Promise<ChatReply> {
    await wait(1100)
    const hit = CANNED.find((c) => c.match.test(message))
    return { conversation_id: conversation_id ?? 'demo-conv', ...(hit?.reply ?? NOT_COVERED) }
  },

  async nextQuestion(course: Course): Promise<Question> {
    await wait(500)
    const list = QUESTIONS[course]
    const q = list[qIndex[course] % list.length]
    qIndex = { ...qIndex, [course]: qIndex[course] + 1 }
    const { _answer, _expl, ...visible } = q
    void _answer; void _expl
    return visible
  },

  async answer(question_id: string, answer: string): Promise<AnswerResult> {
    await wait(900)
    const q = Object.values(QUESTIONS).flat().find((x) => x.id === question_id)!
    const src = [{ title: `${q.topic_name} · lecture slides · p.${12 + q.question.length % 20}`, source: '#' }]
    if (q.kind === 'mcq') {
      const right = answer.trim().toLowerCase() === q._answer.toLowerCase()
      return { score: right ? 2 : 0, max_score: 2, feedback: q._expl, missing_points: [],
               answer: q._answer, explanation: q._expl, sources: src }
    }
    const words = answer.trim().split(/\s+/).length
    const score = words > 18 ? 2 : words > 6 ? 1 : 0
    return {
      score, max_score: 2,
      feedback: score === 2
        ? 'Covers the key idea and says why it matters. Good.'
        : score === 1
          ? 'Right direction, but you didn\'t say what makes the two approaches differ step by step.'
          : 'This misses the main idea. Read the reference answer and try it again tomorrow.',
      missing_points: score === 2 ? [] : ['what each iteration actually updates', 'when each one stops'],
      answer: q._answer, explanation: '', sources: src,
    }
  },

  async documents() {
    await wait(250)
    return { documents: docs, queue }
  },

  async upload(file: File, course: Course) {
    await wait(400)
    docs.unshift({ id: `u${Date.now()}`, filename: file.name, course_id: course, status: 'queued',
                   pages: null, chunks: 0, error: null })
    queue.pending += 1
    return { document_id: 'demo', status: 'queued' }
  },

  async progress(course?: Course): Promise<Progress> {
    await wait(300)
    if (!course) return progress
    return {
      ...progress,
      weakest: progress.weakest.filter((t) => t.course_id === course),
      mastery: progress.mastery.filter((t) => t.course_id === course),
    }
  },
}
