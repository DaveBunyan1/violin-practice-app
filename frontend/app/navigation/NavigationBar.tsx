"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/practice", label: "Practice" },
  { href: "/repertoire", label: "Repertoire" },
  { href: "/analytics", label: "Analytics" },
  { href: "/settings", label: "Settings" },
];

export default function NavigationBar() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        display: "flex",
        alignItems: "center",
        gap: 24,
        padding: "16px 32px",
        background: "#1d1d1d",
        borderBottom: "1px solid #333",
      }}
    >
      <h2
        style={{
          margin: 0,
          marginRight: 32,
          color: "#BB86FC",
        }}
      >
        🎻 Practice Studio
      </h2>

      {links.map((link) => {
        const active = pathname === link.href;

        return (
          <Link
            key={link.href}
            href={link.href}
            style={{
              color: active ? "#BB86FC" : "#ddd",
              textDecoration: "none",
              fontWeight: active ? 700 : 500,
              paddingBottom: 4,
              borderBottom: active
                ? "2px solid #BB86FC"
                : "2px solid transparent",
              transition: "0.2s",
            }}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
