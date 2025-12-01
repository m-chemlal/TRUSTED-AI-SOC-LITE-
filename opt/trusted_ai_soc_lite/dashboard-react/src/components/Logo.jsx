import React from 'react';

export function Logo({ size = 52 }) {
  return (
    <svg
      className="logo-mark"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="#7b2cbf"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M12 2L14 5L12 8L10 5L12 2ZM12 8L14 11L12 14L10 11L12 8ZM12 14L14 17L12 20L10 17L12 14Z" />
      <path d="M4 5L10 11M20 5L14 11" stroke="#c77dff" strokeWidth="2" />
      <path d="M4 17L10 11M20 17L14 11" stroke="#c77dff" strokeWidth="2" />
    </svg>
  );
}
