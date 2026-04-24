/**
 * FairGrade AI — Shared TypeScript Interfaces
 * Centralized type definitions for the entire frontend application.
 */

// ─── API Response Types ───

export interface EvaluationResult {
  aiScore: number;
  teacherScore: number;
  explanation: string;
  confidenceScore?: number;
}

export interface BiasResult {
  level: "Low" | "Medium" | "High";
  status: "Fair" | "Undergraded" | "Overgraded";
  gap: number;
  biasScorePercentage?: number;
  confidenceWeight?: number;
  completenessFactor?: number;
  formulaUsed?: string;
}

export interface PipelineWarning {
  agent: string;
  error: string;
}

export interface EvaluationReport {
  originalTextLength: number;
  anonymizedText: string;
  evaluation: EvaluationResult;
  bias: BiasResult;
  verified: boolean;
  pipelineWarnings?: PipelineWarning[];
}

export interface FileResult {
  fileName: string;
  data: EvaluationReport | null;
  error: string | null;
}

// ─── Human-in-the-Loop Types ───

export interface VerifyPayload {
  action: "accept_ai" | "override";
  finalScore: number;
  originalAiScore: number;
  originalTeacherScore: number;
  overrideReason?: string | null;
}

// ─── Component Prop Types ───

export interface DarkModeToggleProps {
  isDark: boolean;
  onToggle: () => void;
}

export interface AnimatedCounterProps {
  end: number | string;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
}

export interface AgentPipelineProps {
  currentStep: number;
  fileName: string;
}

export interface FooterProps {}

export interface ResultCardProps {
  result: FileResult;
  studentId: string;
  onRetry: ((fileName: string) => void) | null;
  onVerify: (fileName: string, data: VerifyPayload) => void;
  truncateName: (name: string, max?: number) => string;
}

export interface EvaluationSetupProps {
  teacherScore: string;
  setTeacherScore: (score: string) => void;
  questionContext: string;
  setQuestionContext: (context: string) => void;
  files: File[];
  studentIds: Record<string, string>;
  handleStudentIdChange: (fileName: string, value: string) => void;
  handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleDrag: (e: React.DragEvent<HTMLDivElement>) => void;
  handleDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  dragActive: boolean;
  removeFile: (fileName: string) => void;
  isProcessing: boolean;
  currentFileIndex: number;
  runAgents: () => void;
  globalError: string;
  truncateName: (name: string, max?: number) => string;
}

// ─── Question Preset Types ───

export interface QuestionPreset {
  name: string;
  context: string;
}

// ─── Firebase Evaluation Document ───

export interface FirestoreEvaluation {
  id: string;
  ai_score: number;
  teacher_score: number;
  bias_status: "Fair" | "Overgraded" | "Undergraded";
  bias_level: string;
  anonymized_text: string;
  explanation: string;
  student_identifier?: string;
  teacher_uid?: string;
  teacher_email?: string;
  timestamp?: { seconds: number; nanoseconds: number };
}
