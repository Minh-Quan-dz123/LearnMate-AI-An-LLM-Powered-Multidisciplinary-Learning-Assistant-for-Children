import React, { useState } from 'react';
import type { ChildProfile, CreateChildPayload } from '../../types/child';
import { COMMON_INTERESTS } from '../../constants/subjects';
import { X, Heart, Sparkles } from 'lucide-react';

interface ChildFormModalProps {
  userId: number;
  editingChild?: ChildProfile | null;
  onClose: () => void;
  onSubmit: (payload: CreateChildPayload) => Promise<void>;
}

export const ChildFormModal: React.FC<ChildFormModalProps> = ({
  userId,
  editingChild,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState(editingChild?.name || '');
  const [age, setAge] = useState<number>(editingChild?.age || 7);
  const [gender, setGender] = useState<string>(editingChild?.gender || 'Nữ');
  const [interests, setInterests] = useState<string[]>(editingChild?.interests || []);
  const [customInterest, setCustomInterest] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleInterest = (item: string) => {
    if (interests.includes(item)) {
      setInterests(interests.filter((i) => i !== item));
    } else {
      setInterests([...interests, item]);
    }
  };

  const handleAddCustomInterest = () => {
    const trimmed = customInterest.trim();
    if (trimmed && !interests.includes(trimmed)) {
      setInterests([...interests, trimmed]);
      setCustomInterest('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Con hãy nhập tên hoặc biệt danh nhé!');
      return;
    }
    if (age < 3 || age > 15) {
      setError('Độ tuổi phù hợp là từ 3 đến 15 tuổi.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        user_id: userId,
        name: name.trim(),
        age: Number(age),
        gender,
        interests,
      });
      onClose();
    } catch {
      setError('Không thể lưu hồ sơ. Vui lòng thử lại!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="card"
        style={{ maxWidth: '500px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles color="var(--color-accent)" size={24} />
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
              {editingChild ? 'Chỉnh sửa hồ sơ bé' : 'Thêm hồ sơ bé mới'}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
          >
            <X size={24} />
          </button>
        </div>

        {error && (
          <div style={{
            backgroundColor: '#FFF5F5',
            color: '#E03131',
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '16px',
            fontSize: '0.9rem',
            fontWeight: 700
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 700, marginBottom: '6px' }}>
              Tên hoặc biệt danh của bé *
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="Ví dụ: Bé An, Bo Bo, Sóc Con..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 700, marginBottom: '6px' }}>
                Tuổi của bé (3–15) *
              </label>
              <input
                type="number"
                min={3}
                max={15}
                className="input-field"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                disabled={loading}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: 700, marginBottom: '6px' }}>
                Giới tính
              </label>
              <select
                className="input-field"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                disabled={loading}
              >
                <option value="Nữ">Bé gái (Nữ)</option>
                <option value="Nam">Bé trai (Nam)</option>
                <option value="Không muốn cung cấp">Khác / Chưa chọn</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 700, marginBottom: '8px' }}>
              <Heart size={16} style={{ display: 'inline', marginRight: '6px', color: 'var(--color-primary)' }} />
              Sở thích của bé (giúp AI ra đề vui hơn)
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
              {COMMON_INTERESTS.map((item) => {
                const isSelected = interests.includes(item);
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleInterest(item)}
                    style={{
                      padding: '8px 14px',
                      borderRadius: 'var(--radius-full)',
                      border: isSelected ? '2px solid var(--color-primary)' : '2px solid var(--color-border)',
                      backgroundColor: isSelected ? '#FFE3E3' : '#F8F9FA',
                      color: isSelected ? 'var(--color-primary)' : 'var(--color-text-main)',
                      fontWeight: 700,
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {item} {isSelected && '✓'}
                  </button>
                );
              })}
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                className="input-field"
                placeholder="Thêm sở thích khác..."
                value={customInterest}
                onChange={(e) => setCustomInterest(e.target.value)}
                style={{ padding: '10px 14px', fontSize: '0.95rem' }}
              />
              <button
                type="button"
                className="btn btn-outline"
                onClick={handleAddCustomInterest}
                style={{ padding: '10px 18px', whiteSpace: 'nowrap' }}
              >
                Thêm
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={loading}
              style={{ flex: 1 }}
            >
              Hủy
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ flex: 1 }}
            >
              {loading ? 'Đang lưu...' : 'Lưu hồ sơ'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
