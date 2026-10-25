import { useState } from 'react';
import { authService } from './services/authService';
import type { User } from './types/auth';
import type { ChildProfile } from './types/child';
import { AuthPage } from './views/auth/AuthPage';
import { ChildSelectPage } from './views/profiles/ChildSelectPage';
import { Sparkles, BookOpen, RotateCcw } from 'lucide-react';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => authService.getCurrentUser());
  const [activeChild, setActiveChild] = useState<ChildProfile | null>(null);

  const handleLogout = () => {
    authService.logout();
    setCurrentUser(null);
    setActiveChild(null);
  };

  const handleSelectChild = (child: ChildProfile) => {
    setActiveChild(child);
  };

  const handleChangeChild = () => {
    setActiveChild(null);
  };

  // 1. Chưa đăng nhập -> Vào AuthPage
  if (!currentUser) {
    return <AuthPage onAuthSuccess={(user) => setCurrentUser(user)} />;
  }

  // 2. Đã đăng nhập nhưng chưa chọn bé -> Vào ChildSelectPage
  if (!activeChild) {
    return (
      <ChildSelectPage
        user={currentUser}
        onSelectChild={handleSelectChild}
        onLogout={handleLogout}
      />
    );
  }

  // 3. Đã chọn bé -> Hiển thị Header đang học cùng bé & Chỗ trống cho Luồng 2 (Làm bài tập)
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* App Header */}
      <header style={{
        backgroundColor: 'white',
        borderBottom: '2px solid var(--color-border)',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: 'var(--shadow-sm)'
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            backgroundColor: '#FFE3E3',
            color: 'var(--color-primary)',
            padding: '8px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center'
          }}>
            <Sparkles size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, lineHeight: 1.1 }}>LearnMate AI</h2>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)' }}>
              Trợ lý học tập thông minh
            </span>
          </div>
        </div>

        {/* Thông tin bé đang học + Nút đổi bé */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            backgroundColor: '#F8F9FA',
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            border: '2px solid var(--color-border)'
          }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              backgroundColor: activeChild.gender === 'Nữ' ? '#F783AC' : '#4DABF7',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '0.85rem'
            }}>
              {activeChild.name.charAt(0)}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 800 }}>{activeChild.name}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                {activeChild.age} tuổi
              </span>
            </div>
          </div>

          <button
            onClick={handleChangeChild}
            className="btn btn-outline"
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            <RotateCcw size={15} />
            <span>Đổi bé</span>
          </button>
        </div>
      </header>

      {/* Main Content Area: Chuẩn bị nối tiếp sang Luồng 2 (Làm bài tập) */}
      <main style={{ flex: 1, padding: '32px 20px', maxWidth: '860px', margin: '0 auto', width: '100%' }}>
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '72px',
            height: '72px',
            borderRadius: '24px',
            backgroundColor: '#E7F5FF',
            color: 'var(--color-secondary)',
            marginBottom: '16px'
          }}>
            <BookOpen size={40} />
          </div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '8px' }}>
            Chào mừng {activeChild.name} đến với bài học! 🎉
          </h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '1.05rem', fontWeight: 600, maxWidth: '540px', margin: '0 auto 24px' }}>
            Luồng 1 (Đăng ký, Đăng nhập và Quản lý hồ sơ trẻ) đã hoàn thành xuất sắc! Tiếp theo sẽ là màn hình Cấu hình môn học và Trình làm bài tập AI.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
