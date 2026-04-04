import "./globals.css";

export const metadata = {
  title: "Splitwise Clone",
  description: "A premium splitwise frontend UI",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
