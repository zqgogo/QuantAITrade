import { ReactNode } from 'react';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: ReactNode;
  currentPage: string;
}

export default function Layout({ children, currentPage }: LayoutProps) {
  return (
    <div className="flex min-h-screen bg-dark-900">
      <Sidebar currentPage={currentPage} />
      <main className="flex-1 overflow-auto scrollbar-thin">
        {children}
      </main>
    </div>
  );
}
