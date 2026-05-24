export type NavItem = {
  href: string;
  label: string;
  kbd: string;
};

export const navigationItems: NavItem[] = [
  { href: "/", label: "系统总览", kbd: "00" },
  { href: "/today-operations", label: "今日作战台", kbd: "01" },
  { href: "/theme-mainlines", label: "题材主线", kbd: "02" },
  { href: "/signal-detail", label: "信号详情", kbd: "03" },
  { href: "/backtest", label: "回测稳健性", kbd: "04" },
  { href: "/review", label: "复盘记录", kbd: "05" },
];

