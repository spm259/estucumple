import Image from 'next/image'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-green-400 to-green-600 text-white">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm lg:flex flex-col">
        <h1 className="text-5xl font-bold mb-8 text-center">Recordatorio de Cumpleaños</h1>
        <p className="text-2xl mb-8 text-center">¡Próximamente!</p>
        <Image
          src="/whatsapp-logo.png"
          alt="WhatsApp Logo"
          width={100}
          height={100}
          className="mb-8"
        />
        <p className="text-xl mb-8 text-center max-w-2xl">
          Nunca más te olvidarás de un cumpleaños. Envía los nombres y fechas de cumpleaños de tus contactos por WhatsApp y recibe recordatorios oportunos.
        </p>
        <Button className="bg-white text-green-600 hover:bg-green-100">
          Mantente Informado
        </Button>
      </div>
    </main>
  )
}

