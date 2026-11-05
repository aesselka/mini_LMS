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
export function errorText(err: any, fallback = 'Something went wrong. Please try again.'): string {
  const body = err?.error;
  if (err?.status === 0) return 'Cannot reach the server. Is the backend running?';
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
