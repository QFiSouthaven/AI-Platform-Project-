import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  ShieldCheckIcon,
  CubeTransparentIcon,
  CpuChipIcon,
  CircleStackIcon,
  CubeIcon,
  ServerStackIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'User Gateway', href: '/gateway', icon: ShieldCheckIcon },
  { name: 'Workflows', href: '/workflows', icon: CubeTransparentIcon },
  { name: 'Processing', href: '/processing', icon: CpuChipIcon },
  { name: 'Data Integration', href: '/data', icon: CircleStackIcon },
  { name: 'Models', href: '/models', icon: CubeIcon },
  { name: 'Infrastructure', href: '/infrastructure', icon: ServerStackIcon },
]

function Sidebar() {
  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
      {/* Sidebar background with gradient */}
      <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gradient-to-b from-secondary-900 to-secondary-800 px-6 pb-4">
        {/* Logo */}
        <div className="flex h-16 shrink-0 items-center">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary-400 to-primary-600">
              <CpuChipIcon className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">AI Platform</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-1">
                {navigation.map((item) => (
                  <li key={item.name}>
                    <NavLink
                      to={item.href}
                      className={({ isActive }) =>
                        `group flex gap-x-3 rounded-lg p-3 text-sm font-medium leading-6 transition-all duration-200 ${
                          isActive
                            ? 'bg-primary-600 text-white shadow-lg'
                            : 'text-gray-300 hover:bg-secondary-700 hover:text-white'
                        }`
                      }
                    >
                      <item.icon
                        className="h-6 w-6 shrink-0"
                        aria-hidden="true"
                      />
                      {item.name}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </li>

            {/* Settings at bottom */}
            <li className="mt-auto">
              <NavLink
                to="/settings"
                className={({ isActive }) =>
                  `group -mx-2 flex gap-x-3 rounded-lg p-3 text-sm font-medium leading-6 transition-all duration-200 ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-secondary-700 hover:text-white'
                  }`
                }
              >
                <Cog6ToothIcon
                  className="h-6 w-6 shrink-0"
                  aria-hidden="true"
                />
                Settings
              </NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  )
}

export default Sidebar
