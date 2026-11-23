-- Weights come from the syllabus and my study plans. Bump a weight when the
-- professor spends a whole lecture on something.
INSERT INTO topics (id, course_id, name, exam_weight) VALUES
  ('daa.asymptotics',     'daa', 'Asymptotic analysis and recurrences', 1.0),
  ('daa.divide_conquer',  'daa', 'Divide and conquer, master theorem', 1.2),
  ('daa.greedy',          'daa', 'Greedy algorithms and exchange arguments', 1.2),
  ('daa.dp',              'daa', 'Dynamic programming', 1.5),
  ('daa.graphs_basic',    'daa', 'BFS, DFS, topological sort, SCC', 1.0),
  ('daa.shortest_paths',  'daa', 'Shortest paths (Dijkstra, Bellman-Ford, Floyd-Warshall)', 1.3),
  ('daa.mst',             'daa', 'Minimum spanning trees', 1.0),
  ('daa.flow',            'daa', 'Network flow and matching', 1.2),
  ('daa.np',              'daa', 'NP-completeness and reductions', 1.3),

  ('swe.process',         'swe', 'Process models: waterfall, agile, scrum', 1.0),
  ('swe.requirements',    'swe', 'Requirements, user stories, use cases', 1.1),
  ('swe.uml',             'swe', 'UML: class, sequence and state diagrams', 1.2),
  ('swe.design',          'swe', 'Design principles: SOLID, coupling, cohesion', 1.3),
  ('swe.patterns',        'swe', 'Design patterns', 1.4),
  ('swe.architecture',    'swe', 'Architecture styles and microservices', 1.1),
  ('swe.testing',         'swe', 'Testing: unit, integration, coverage, TDD', 1.3),
  ('swe.vcs_ci',          'swe', 'Version control, CI/CD, DevOps', 0.9),
  ('swe.estimation',      'swe', 'Estimation, project management, risk', 0.8),

  ('ai.search',           'ai',  'Uninformed and informed search, A*', 1.3),
  ('ai.adversarial',      'ai',  'Adversarial search, minimax, alpha-beta', 1.2),
  ('ai.csp',              'ai',  'Constraint satisfaction', 1.1),
  ('ai.logic',            'ai',  'Propositional and first-order logic', 1.1),
  ('ai.probability',      'ai',  'Probability and Bayesian networks', 1.3),
  ('ai.mdp_rl',           'ai',  'MDPs and reinforcement learning', 1.4),
  ('ai.ml',               'ai',  'Supervised learning basics', 1.0),
  ('ai.neural',           'ai',  'Neural networks', 1.0)
ON CONFLICT (id) DO NOTHING;

INSERT INTO topic_stats (topic_id) SELECT id FROM topics ON CONFLICT DO NOTHING;
