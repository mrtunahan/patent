import { Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import Applicants from './pages/Applicants'
import AttorneyFirms from './pages/AttorneyFirms'
import Departments from './pages/Departments'
import NotFound from './pages/NotFound'
import PatentForm from './pages/PatentForm'
import PatentList from './pages/PatentList'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<PatentList />} />
        <Route path="patents/new" element={<PatentForm />} />
        <Route path="patents/:id" element={<PatentForm />} />
        <Route path="applicants" element={<Applicants />} />
        <Route path="departments" element={<Departments />} />
        <Route path="attorney-firms" element={<AttorneyFirms />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
