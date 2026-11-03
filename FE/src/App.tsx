import { useState } from 'react';
import { authService } from './services/authService';
import type { User } from './types/auth';
import type { ChildProfile } from './types/child';
import { AuthPage } from './views/auth/AuthPage';
import { ChildSelectPage } from './views/profiles/ChildSelectPage';
import { Sparkles, RotateCcw } from 'lucide-react';
import { ExercisePage } from './views/exercise/ExercisePage';
import { ActivitySelect } from './views/activities/ActivitySelect';
import { DetectivePage } from './views/detective/DetectivePage';


export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => authService.getCurrentUser());
  const [activeChild, setActiveChild] = useState<ChildProfile | null>(null);

  // choose: chọn hoạt động
  // learn: Module 1–2
  // detective: Module 3
  const [activeActivity, setActiveActivity] = useState<'choose' | 'learn' | 'detective'>('choose');

  const handleLogout = () => {
    authService.logout();
    setCurrentUser(null);
    setActiveChild(null);
    setActiveActivity('choose');
  };

  const handleSelectChild = (child: ChildProfile) => {
    setActiveChild(child);
    setActiveActivity('choose');
  };

  const handleChangeChild = () => {
    setActiveChild(null);
    setActiveActivity('choose');
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
      {/* Màn hình cấu hình, làm và chấm bài */}
      {/* Màn hình chọn hoạt động hoặc module đã chọn */}
      {activeActivity === 'choose' && (
        <ActivitySelect
          child={activeChild}
          onChooseLearning={() => setActiveActivity('learn')}
          onChooseDetective={() => setActiveActivity('detective')}
        />
      )}

      {activeActivity === 'learn' && (
        <ExercisePage
          key={activeChild.child_id}
          child={activeChild}
          onGoHome={() => setActiveActivity('choose')}
        />
      )}

      {activeActivity === 'detective' && (
        <DetectivePage
          child={activeChild}
          onBackToActivities={() => setActiveActivity('choose')}
        />
      )}
    </div>
  );
}

export default App;
