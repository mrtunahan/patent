import { Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import Applicants from './pages/Applicants'
import AttorneyFirms from './pages/AttorneyFirms'
import Departments from './pages/Departments'
import NotFound from './pages/NotFound'
import Partners from './pages/Partners'
import PatentList from './pages/PatentList'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        {/* Çekmece (yeni/düzenle) PatentList içinde açılır; adres yenilemede de çalışır. */}
        <Route index element={<PatentList />} />
        <Route path="patents/new" element={<PatentList />} />
        <Route path="patents/:id" element={<PatentList />} />
        <Route path="applicants" element={<Applicants />} />
        <Route path="departments" element={<Departments />} />
        <Route path="attorney-firms" element={<AttorneyFirms />} />
        <Route path="partners" element={<Partners />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
