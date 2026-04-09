import { cn } from "@/lib/utils";

export function NeoButton({ 
  children, 
  className, 
  variant = "primary", 
  ...props 
}) {
  const baseStyles = "h-14 px-8 border-4 border-black font-bold text-sm uppercase tracking-wide transition-all duration-100 active:translate-x-neo-push active:translate-y-neo-push active:shadow-none flex items-center justify-center";
  
  const variants = {
    primary: "bg-neo-accent text-black shadow-neo hover:brightness-90",
    secondary: "bg-neo-secondary text-black shadow-neo hover:brightness-90",
    outline: "bg-white text-black shadow-neo hover:bg-gray-100",
    ghost: "border-2 border-transparent hover:border-black text-black",
  };

  return (
    <button 
      className={cn(baseStyles, variants[variant], className)}
      {...props}
    >
      {children}
    </button>
  );
}
