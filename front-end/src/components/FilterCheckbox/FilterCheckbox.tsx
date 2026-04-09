'use client';
import styles from './FilterCheckbox.module.css';

interface FilterOption {
  id: string;
  label: string;
  colorDot?: string;
  count?: number;
}

interface FilterCheckboxGroupProps {
  groupLabel: string;
  options: FilterOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

export function FilterCheckboxGroup({ groupLabel, options, selected, onChange }: FilterCheckboxGroupProps) {
  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);
  };

  return (
    <div className={styles.group}>
      <p className={styles.groupLabel}>{groupLabel}</p>
      {options.map((opt) => {
        const checked = selected.includes(opt.id);
        return (
          <label key={opt.id} className={styles.item}>
            <input
              type="checkbox"
              style={{ display: 'none' }}
              checked={checked}
              onChange={() => toggle(opt.id)}
              id={`filter-${opt.id}`}
            />
            <span className={`${styles.checkbox} ${checked ? styles.checked : ''}`}>
              {checked && <span className={styles.checkmark}>✓</span>}
            </span>
            {opt.colorDot && (
              <span className={styles.colorDot} style={{ background: opt.colorDot }} aria-hidden="true" />
            )}
            <span className={styles.label}>{opt.label}</span>
            {opt.count !== undefined && (
              <span className={styles.count}>{opt.count}</span>
            )}
          </label>
        );
      })}
    </div>
  );
}
