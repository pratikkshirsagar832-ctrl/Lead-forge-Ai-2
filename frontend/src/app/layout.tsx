import type { Metadata } from 'next';
import { Inter, Space_Grotesk } from 'next/font/google';
import Script from 'next/script';
import '../styles/globals.css';
import { ThemeProvider } from '@/components/ThemeProvider';
import { ToastContainer } from '@/components/shared/Toast';
import { AnimatedBackground } from '@/components/AnimatedBackground';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-heading', weight: ['400', '500', '600', '700'] });


export const metadata: Metadata = {
  title: 'Hyperclients',
  description: 'Automated Lead Generation Engine',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning>
      <body className={`${inter.className} ${spaceGrotesk.variable} min-h-screen bg-navy text-ice antialiased selection:bg-violet/30 selection:text-offwhite`}>
          <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AnimatedBackground />
          {children}
          <ToastContainer />
        </ThemeProvider>
      </body>
    </html>
  );
}
