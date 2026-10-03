import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'Avialog · Inteligência de Transporte',description:'Planejamento de cargas, simulação de frota e qualidade do transporte de aves.',icons:{icon:'/favicon.svg',shortcut:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="pt-BR"><body>{children}</body></html>}
