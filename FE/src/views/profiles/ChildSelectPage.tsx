import React, { useEffect, useState } from 'react';
import { childService } from '../../services/childService';
import type { ChildProfile, CreateChildPayload } from '../../types/child';
import type { User } from '../../types/auth';
import { ChildFormModal } from './ChildFormModal';
import { UserCheck, Plus, Edit2, Trash2, ArrowRight, LogOut, Award } from 'lucide-react';

interface ChildSelectPageProps {
  user: User;
  onSelectChild: (child: ChildProfile) => void;
  onLogout: () => void;
}

export const ChildSelectPage: React.FC<ChildSelectPageProps> = ({
  user,
  onSelectChild,
  onLogout,
}) => {
  const [children, setChildren] = useState<ChildProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingChild, setEditingChild] = useState<ChildProfile | null>(null);

  const fetchChildren = async () => {
    setLoading(true);
    const res = await childService.getChildren(user.user_id);
    if (res.success && res.data) {
      setChildren(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchChildren();
  }, [user.user_id]);

  const handleSaveChild = async (payload: CreateChildPayload) => {
    if (editingChild) {
      await childService.updateChild({
        ...payload,
        child_id: editingChild.child_id,
      });
    } else {
      await childService.createChild(payload);
    }
    fetchChildren();
  };

  const handleDeleteChild = async (childId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Con hoặc bố mẹ có chắc muốn xóa hồ sơ này không?')) {
      await childService.deleteChild(childId, user.user_id);
      fetchChildren();
    }
  };

  const openCreateModal = () => {
    setEditingChild(null);
    setShowModal(true);
  };

  const openEditModal = (child: ChildProfile, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingChild(child);
    setShowModal(true);
  };

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto', padding: '32px 20px' }}>
      {/* Top Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '32px',
        backgroundColor: 'white',
        padding: '16px 24px',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: '#E7F5FF',
            color: 'var(--color-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <UserCheck size={22} />
          </div>
          <div>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Tài khoản</span>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>{user.username}</h3>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="btn btn-outline"
          style={{ padding: '8px 16px', fontSize: '0.9rem', color: '#FA5252' }}
        >
          <LogOut size={16} />
          <span>Đăng xuất</span>
        </button>
      </div>

      {/* Title */}
      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-text-main)', marginBottom: '8px' }}>
          Hôm nay ai sẽ cùng học với LearnMate? 🚀
        </h1>
        <p style={{ color: 'var(--color-text-muted)', fontWeight: 600, fontSize: '1.1rem' }}>
          Chọn hồ sơ của bé hoặc thêm bé mới để AI tạo bài học phù hợp lứa tuổi nhé!
        </p>
      </div>

      {/* Danh sách bé */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', fontWeight: 700, color: 'var(--color-text-muted)' }}>
          Đang tải danh sách người học...
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: '20px',
          marginBottom: '28px'
        }}>
          {children.map((child) => (
            <div
              key={child.child_id}
              className="card"
              onClick={() => {
                childService.setActiveChildId(child.child_id);
                onSelectChild(child);
              }}
              style={{
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                border: '2px solid transparent',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.borderColor = 'var(--color-secondary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = 'transparent';
              }}
            >
              {/* Action Buttons: Sửa & Xóa */}
              <div style={{ position: 'absolute', top: '16px', right: '16px', display: 'flex', gap: '6px' }}>
                <button
                  onClick={(e) => openEditModal(child, e)}
                  title="Sửa hồ sơ"
                  style={{
                    background: '#F1F3F5',
                    border: 'none',
                    borderRadius: '8px',
                    width: '32px',
                    height: '32px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    color: 'var(--color-text-muted)'
                  }}
                >
                  <Edit2 size={16} />
                </button>
                <button
                  onClick={(e) => handleDeleteChild(child.child_id, e)}
                  title="Xóa hồ sơ"
                  style={{
                    background: '#FFF5F5',
                    border: 'none',
                    borderRadius: '8px',
                    width: '32px',
                    height: '32px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    color: '#FA5252'
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <div>
                {/* Avatar Icon */}
                <div style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '20px',
                  backgroundColor: child.gender === 'Nữ' ? '#FFF0F6' : '#E7F5FF',
                  color: child.gender === 'Nữ' ? '#F783AC' : '#4DABF7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px'
                }}>
                  <Award size={32} />
                </div>

                <h3 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '4px' }}>
                  {child.name}
                </h3>
                <div style={{
                  display: 'inline-block',
                  backgroundColor: '#F8F9FA',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: 'var(--color-text-muted)',
                  marginBottom: '12px'
                }}>
                  {child.age} tuổi • {child.gender || 'Bé'}
                </div>

                {/* Sở thích */}
                {child.interests && child.interests.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                    {child.interests.slice(0, 3).map((item) => (
                      <span
                        key={item}
                        style={{
                          fontSize: '0.8rem',
                          fontWeight: 700,
                          backgroundColor: '#F1F3F5',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          color: '#495057'
                        }}
                      >
                        #{item}
                      </span>
                    ))}
                    {child.interests.length > 3 && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 700 }}>
                        +{child.interests.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Nút Vào Học */}
              <div style={{
                marginTop: '20px',
                paddingTop: '16px',
                borderTop: '1px solid var(--color-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                color: 'var(--color-secondary)',
                fontWeight: 800
              }}>
                <span>Vào học ngay</span>
                <ArrowRight size={18} />
              </div>
            </div>
          ))}

          {/* Thẻ Thêm Bé Mới */}
          <div
            className="card"
            onClick={openCreateModal}
            style={{
              cursor: 'pointer',
              border: '2px dashed #CED4DA',
              backgroundColor: 'transparent',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px 20px',
              minHeight: '220px',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'white';
              e.currentTarget.style.borderColor = 'var(--color-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.borderColor = '#CED4DA';
            }}
          >
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: '#FFE3E3',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px'
            }}>
              <Plus size={28} />
            </div>
            <span style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--color-text-main)' }}>
              Thêm hồ sơ bé mới
            </span>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '4px', fontWeight: 600 }}>
              Cài đặt tên, tuổi & sở thích
            </span>
          </div>
        </div>
      )}

      {/* Modal Thêm / Sửa */}
      {showModal && (
        <ChildFormModal
          userId={user.user_id}
          editingChild={editingChild}
          onClose={() => setShowModal(false)}
          onSubmit={handleSaveChild}
        />
      )}
    </div>
  );
};
