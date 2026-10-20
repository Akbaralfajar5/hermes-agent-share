---
name: state-management-react
description: React state management patterns — when to use useState, useReducer, Context, Zustand, Jotai, or server state (React Query/SWR). Use when building complex React/Next.js apps where prop drilling becomes painful, when choosing a state library, or when state architecture decisions need to be made.
---

# State Management in React

## Overview

Most React apps use too much state management. Start with the simplest solution and escalate only when you hit a real problem. The best state management is the one you barely notice.

## Decision Flowchart

```
Where does the state live?
│
├─ Only 1 component needs it?
│  └─ useState / useReducer
│
├─ Parent + direct children?
│  └─ Lift state up (props)
│
├─ Distant siblings / deep tree?
│  ├─ Read-heavy, infrequent updates?
│  │  └─ React Context
│  └─ Frequent updates / performance critical?
│     └─ Zustand (recommended) or Jotai
│
├─ Server data (API responses)?
│  └─ React Query / SWR (NEVER store in client state)
│
└─ URL state (filters, pagination, search)?
   └─ URL params (useSearchParams / router)
```

## The Golden Rule

**Server state is NOT client state.** API responses, database records, user lists — these are server state. Use React Query/SWR to cache them. Never manually store API responses in useState/Zustand.

```typescript
// BAD: manual server state management
const [users, setUsers] = useState([]);
useEffect(() => {
  fetch('/api/users').then(r => r.json()).then(setUsers);
}, []);

// GOOD: React Query handles caching, refetching, stale-while-revalidate
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: () => fetch('/api/users').then(r => r.json()),
});
```

## Level 1: Built-in React

### useState

Simple local state. Default choice.

```typescript
const [count, setCount] = useState(0);
const [isOpen, setIsOpen] = useState(false);
const [form, setForm] = useState({ name: '', email: '' });
```

### useReducer

Complex state with multiple related updates. Good for forms, wizards, state machines.

```typescript
type State = { step: number; data: FormData; errors: string[] };
type Action =
  | { type: 'NEXT' }
  | { type: 'PREV' }
  | { type: 'SET_DATA'; payload: Partial<FormData> }
  | { type: 'SET_ERRORS'; payload: string[] };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'NEXT': return { ...state, step: state.step + 1, errors: [] };
    case 'PREV': return { ...state, step: state.step - 1, errors: [] };
    case 'SET_DATA': return { ...state, data: { ...state.data, ...action.payload } };
    case 'SET_ERRORS': return { ...state, errors: action.payload };
  }
}

const [state, dispatch] = useReducer(reducer, { step: 0, data: {}, errors: [] });
```

### Lifting State Up

When two siblings need the same state, lift it to their parent.

```typescript
// Parent owns the state
function TaskPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  return (
    <>
      <TaskForm onAdd={(t) => setTasks([...tasks, t])} />
      <TaskList tasks={tasks} onDelete={(id) => setTasks(tasks.filter(t => t.id !== id))} />
    </>
  );
}
```

## Level 2: Context API

For read-heavy state that changes infrequently. NOT for high-frequency updates.

```typescript
// Theme, auth, locale — perfect for Context
const ThemeContext = createContext<'light' | 'dark'>('light');

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  );
}

// Usage
const theme = useContext(ThemeContext);
```

### Context Anti-Patterns

```typescript
// BAD: Context for high-frequency updates (re-renders everything)
const MousePositionContext = createContext({ x: 0, y: 0 });
// Every mouse move re-renders ALL consumers!

// GOOD: useRef + direct DOM for high-frequency updates
const ref = useRef<HTMLDivElement>(null);
useEffect(() => {
  const handler = (e: MouseEvent) => {
    if (ref.current) ref.current.style.transform = `translate(${e.x}px, ${e.y}px)`;
  };
  window.addEventListener('mousemove', handler);
  return () => window.removeEventListener('mousemove', handler);
}, []);
```

## Level 3: Zustand (Recommended)

Lightweight (1KB), no boilerplate, works outside React, great TypeScript support.

```typescript
import { create } from 'zustand';

interface TaskStore {
  tasks: Task[];
  filter: 'all' | 'active' | 'done';
  addTask: (task: Task) => void;
  removeTask: (id: string) => void;
  setFilter: (filter: TaskStore['filter']) => void;
  filteredTasks: () => Task[];
}

const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  filter: 'all',
  addTask: (task) => set((s) => ({ tasks: [...s.tasks, task] })),
  removeTask: (id) => set((s) => ({ tasks: s.tasks.filter(t => t.id !== id) })),
  setFilter: (filter) => set({ filter }),
  filteredTasks: () => {
    const { tasks, filter } = get();
    if (filter === 'active') return tasks.filter(t => !t.done);
    if (filter === 'done') return tasks.filter(t => t.done);
    return tasks;
  },
}));

// Usage — only re-renders when selected slice changes
function TaskList() {
  const tasks = useTaskStore((s) => s.filteredTasks());
  const remove = useTaskStore((s) => s.removeTask);
  // ...
}
```

### Zustand Persistence

```typescript
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set) => ({ theme: 'dark', setTheme: (t: string) => set({ theme: t }) }),
    { name: 'app-settings' } // localStorage key
  )
);
```

### Zustand Slices (for large stores)

```typescript
const useStore = create<TaskSlice & AuthSlice>()((...a) => ({
  ...createTaskSlice(...a),
  ...createAuthSlice(...a),
}));
```

## Level 4: Jotai (Atomic)

Bottom-up state. Good when you have many independent pieces of state.

```typescript
import { atom, useAtom } from 'jotai';

const filterAtom = atom('all');
const tasksAtom = atom<Task[]>([]);
const filteredTasksAtom = atom((get) => {
  const tasks = get(tasksAtom);
  const filter = get(filterAtom);
  if (filter === 'active') return tasks.filter(t => !t.done);
  return tasks;
});

// Usage
function TaskList() {
  const [tasks] = useAtom(filteredTasksAtom);
  // ...
}
```

### Zustand vs Jotai

| | Zustand | Jotai |
|---|---|---|
| Model | Single store, slices | Atoms (bottom-up) |
| Bundle | ~1KB | ~2KB |
| DevTools | Yes | Yes |
| Persistence | Built-in middleware | Plugin |
| Best for | App-wide stores | Many independent states |
| Outside React | Yes | No (needs Provider) |

**Default recommendation: Zustand** unless you have a specific atomic pattern.

## Server State: React Query / SWR

```typescript
// React Query (TanStack Query) — recommended
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function TaskList() {
  const queryClient = useQueryClient();

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => fetch('/api/tasks').then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const addTask = useMutation({
    mutationFn: (newTask: NewTask) =>
      fetch('/api/tasks', { method: 'POST', body: JSON.stringify(newTask) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });
}
```

### When to Use React Query

```
✅ Data comes from API/database
✅ Data can become stale
✅ Multiple components need same data
✅ You need loading/error states
✅ Optimistic updates

❌ Form state (local)
❌ UI state (modals, tabs)
❌ Animation state
❌ Data that never changes (use constants)
```

## URL State

Filters, pagination, search — store in URL, not state.

```typescript
// Next.js App Router
import { useSearchParams, useRouter } from 'next/navigation';

function TaskFilter() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const filter = searchParams.get('filter') ?? 'all';

  const setFilter = (f: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('filter', f);
    router.push(`?${params.toString()}`);
  };
}
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "I'll use Redux for everything" | Redux is 12KB+ of boilerplate for problems Zustand solves in 1KB |
| "Context is fine for all state" | Context re-renders all consumers on every update. Use for read-heavy, low-frequency |
| "I need global state for the whole app" | Most state is local. Only truly shared state needs global store |
| "I'll store API response in useState" | Use React Query. Manual caching is reinventing a solved problem |
| "Zustand is too simple for complex apps" | Simple is the point. Complexity should live in your business logic, not state management |

## Red Flags

- Prop drilling more than 2-3 levels deep
- useEffect to sync server data into state
- Multiple useState calls that always update together
- Context value changing on every render
- Redux/Zustand store with >20 actions that could be split
- State stored in both URL and React state (pick one)

## Verification

- [ ] Server data uses React Query/SWR, not manual useState
- [ ] URL state (filters, search) stored in URL params
- [ ] Global state only for truly shared state (auth, theme, cart)
- [ ] No prop drilling >3 levels deep
- [ ] Zustand slices used to avoid monolithic stores
- [ ] Context only for read-heavy, low-frequency updates
- [ ] Component state preferred over global state by default
