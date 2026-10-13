export function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <rect width="40" height="40" rx="8" fill="#0b5a3a" />
      <path d="M8 27h24" stroke="#d4e9dc" strokeWidth="2" />
      <path d="M8 31h24" stroke="#d4e9dc" strokeWidth="2" opacity=".55" />
      <path d="M12 23V14l8-5 8 5v9" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinejoin="round" />
      <path d="m16.5 17.5 2.6 2.6 4.8-5" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
