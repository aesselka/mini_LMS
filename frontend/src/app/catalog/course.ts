export interface Teacher {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
}

export interface Course {
  id: number;
  code: string;
  title: string;
  description: string | null;
  credits: number;
  teacher: Teacher;
  students_count: number;
  created_at: string;
}

export interface Enrollment {
  id: number;
  student: string;
  course: number;
  course_title: string;
  enroll_date: string;
  grade: string | null;
}

export function teacherName(t: Teacher): string {
  const full = `${t.first_name} ${t.last_name}`.trim();
  return full || t.username;
}

// DRF sends errors as {"non_field_errors": [...]}, ["..."], {"detail": "..."} or {"field": [...]}
// Returns either a translation key (errors.network, fallback) or the server's own message.
// In templates show it through the pipe: {{ error() | t }} — keys are translated, server text stays as is.
export function errorText(err: any, fallback = 'errors.unknown'): string {
  const body = err?.error;
  if (err?.status === 0) return 'errors.network';
  if (err?.status === 401) return 'errors.sessionExpired';
  if (typeof body === 'string' && body.length < 200) return body;
  if (Array.isArray(body) && body.length) return String(body[0]);
  if (body && typeof body === 'object') {
    if (typeof body.detail === 'string') return body.detail;
    const first = Object.values(body)[0];
    if (Array.isArray(first) && first.length) return String(first[0]);
    if (typeof first === 'string') return first;
  }
  return fallback;
}
