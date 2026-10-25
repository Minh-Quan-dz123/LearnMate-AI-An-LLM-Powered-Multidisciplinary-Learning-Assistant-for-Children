import React, { useState } from 'react';
import { authService } from '../../services/authService';
import type { User } from '../../types/auth';
import { Sparkles, ArrowRight, UserPlus, LogIn, AlertCircle } from 'lucide-react';

interface AuthPageProps {
  onAuthSuccess: (user: User) => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError('Con hãy điền đầy đủ tên đăng nhập và mật khẩu nhé!');
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError('Mật khẩu xác nhận chưa trùng khớp. Con hãy kiểm tra lại nhé!');
      return;
    }

    setLoading(true);

    try {
      if (isRegister) {
        const res = await authService.register({
          username,
          password,
          confirm_password: confirmPassword,
        });
        if (res.success && res.data) {
          onAuthSuccess(res.data);
        } else {
          setError(res.message || 'Đăng ký không thành công.');
        }
      } else {
        const res = await authService.login({ username, password });
        if (res.success && res.data) {
          onAuthSuccess(res.data);
        } else {
          setError(res.message || 'Tên đăng nhập hoặc mật khẩu chưa đúng.');
        }
      }
    } catch {
      setError('Đã xảy ra lỗi kết nối. Hãy thử lại sau!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="card" style={{ maxWidth: '440px', width: '100%' }}>
        {/* Header với linh vật & tiêu đề */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '64px',
            height: '64px',
            borderRadius: '24px',
            backgroundColor: '#FFF4E6',
            color: 'var(--color-primary)',
            marginBottom: '12px'
          }}>
            <Sparkles size={36} />
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--color-text-main)' }}>
            LearnMate AI
          </h1>
          <p style={{ color: 'var(--color-text-muted)', fontWeight: 600, marginTop: '4px' }}>
            {isRegister ? 'Tạo tài khoản học tập vui vẻ' : 'Chào mừng con quay trở lại học tập!'}
          </p>
        </div>

        {/* Thông báo lỗi */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#FFF5F5',
            color: '#E03131',
            padding: '12px 16px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '20px',
            fontSize: '0.95rem',
            fontWeight: 600,
            border: '1px solid #FFC9C9'
          }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Form đăng ký / đăng nhập */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 700, marginBottom: '6px', fontSize: '0.95rem' }}>
              Tên đăng nhập
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="Ví dụ: be_an_01"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 700, marginBottom: '6px', fontSize: '0.95rem' }}>
              Mật khẩu
            </label>
            <input
              type="password"
              className="input-field"
              placeholder="Nhập mật khẩu"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
          </div>

          {isRegister && (
            <div>
              <label style={{ display: 'block', fontWeight: 700, marginBottom: '6px', fontSize: '0.95rem' }}>
                Xác nhận mật khẩu
              </label>
              <input
                type="password"
                className="input-field"
                placeholder="Nhập lại mật khẩu"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
              />
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', marginTop: '8px', padding: '14px', fontSize: '1.1rem' }}
          >
            {loading ? (
              'Đang xử lý...'
            ) : isRegister ? (
              <>
                <UserPlus size={20} />
                <span>Tạo tài khoản</span>
              </>
            ) : (
              <>
                <LogIn size={20} />
                <span>Đăng nhập</span>
                <ArrowRight size={20} />
              </>
            )}
          </button>
        </form>

        {/* Nút chuyển đổi Đăng ký / Đăng nhập */}
        <div style={{ textAlign: 'center', marginTop: '24px', paddingTop: '20px', borderTop: '2px solid var(--color-border)' }}>
          {isRegister ? (
            <p style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>
              Đã có tài khoản?{' '}
              <button
                type="button"
                onClick={() => { setIsRegister(false); setError(null); }}
                style={{ background: 'none', border: 'none', color: 'var(--color-secondary)', fontWeight: 700, cursor: 'pointer', fontSize: '1rem' }}
              >
                Đăng nhập ngay
              </button>
            </p>
          ) : (
            <p style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>
              Chưa có tài khoản?{' '}
              <button
                type="button"
                onClick={() => { setIsRegister(true); setError(null); }}
                style={{ background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 700, cursor: 'pointer', fontSize: '1rem' }}
              >
                Đăng ký tài khoản mới
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
