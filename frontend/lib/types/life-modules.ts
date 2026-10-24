export interface LifeModuleSkillPool {
  kind?: "active" | "knowledge";
  key: string;
  entry_id: string;
  source_skill_id: string;
  source_name: string;
  stage: string;
  before: number;
  grant: number;
  kept: number;
  total: number;
  allocated: number;
  remaining: number;
  unallocatable: number;
  grant_fingerprint: string;
  status: "complete" | "pending" | "invalid" | "unallocatable";
  provisional: boolean;
  candidates: {
    skill_id: string;
    name: string;
    attribute: string;
    specific_required: boolean;
    capacity: number;
    unavailable_reason: string;
  }[];
}

export interface LifeModuleSkillResult {
  version: 2;
  policy: { version: string; active_cap: number; knowledge_cap: number };
  free_active: Record<string, number>;
  free_knowledge: Record<string, number>;
  knowledge_categories?: Record<string, string>;
  native_languages: string[];
  groups: {
    name: string;
    member_free_ratings: Record<string, number>;
    uniform: boolean;
    free_uniform_rating: number | null;
  }[];
  pools: LifeModuleSkillPool[];
  losses: { entry_id: string; skill_key: string; lost: number; reason: string }[];
  purchase_preview?: {
    requested: Record<string, number>;
    totals: Record<string, number>;
    group_totals: Record<string, number>;
    karma: number;
  };
  complete: boolean;
  unavailable_skill_ids?: string[];
  current_active?: Record<string, number>;
  current_knowledge?: Record<string, number>;
  growth_lines?: {
    id: string;
    kind: string;
    target_id: string;
    from_rating: number;
    to_rating: number;
    levels: number;
    karma: number;
  }[];
  frozen: boolean;
  legacy: boolean;
}
