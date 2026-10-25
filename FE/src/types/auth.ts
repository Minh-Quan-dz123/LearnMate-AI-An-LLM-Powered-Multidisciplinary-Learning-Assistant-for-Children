export interface User {
  user_id: number;
  username: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  confirm_password?: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}
