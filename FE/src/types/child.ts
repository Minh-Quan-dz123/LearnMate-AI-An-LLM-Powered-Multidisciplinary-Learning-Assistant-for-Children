export interface ChildProfile {
  child_id: number;
  user_id: number;
  name: string;
  age: number;
  gender?: 'Nam' | 'Nữ' | 'Không muốn cung cấp' | string;
  interests: string[];
  created_at?: string;
  updated_at?: string;
}

export interface CreateChildPayload {
  user_id: number;
  name: string;
  age: number;
  gender?: string;
  interests?: string[];
}

export interface UpdateChildPayload extends CreateChildPayload {
  child_id: number;
}
