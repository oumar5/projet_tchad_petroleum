import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../../about/presentation/about_screen.dart';
import '../../configuration/presentation/configuration_screen.dart';
import '../../dashboard/presentation/dashboard_screen.dart';
import '../../maintenance/presentation/maintenance_screen.dart';
import '../../models/presentation/models_screen_page.dart';
import '../../production/presentation/production_screen.dart';
import '../../water/presentation/water_screen.dart';
import '../auth_controller.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _NavItem {
  const _NavItem(this.icon, this.iconSelected, this.label);
  final IconData icon;
  final IconData iconSelected;
  final String label;
}

const _navItems = <_NavItem>[
  _NavItem(Icons.dashboard_outlined, Icons.dashboard_rounded, 'Dashboard'),
  _NavItem(Icons.list_alt_outlined, Icons.list_alt_rounded, 'Production'),
  _NavItem(Icons.build_outlined, Icons.build_rounded, 'Maintenance'),
  _NavItem(Icons.water_drop_outlined, Icons.water_drop_rounded, 'Injection'),
  _NavItem(Icons.psychology_outlined, Icons.psychology_rounded, 'Modèles IA'),
  _NavItem(Icons.tune_outlined, Icons.tune_rounded, 'Configuration'),
  _NavItem(Icons.info_outline_rounded, Icons.info_rounded, 'À propos'),
];

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _index = 0;

  static const _screens = [
    DashboardScreen(),
    ProductionScreen(),
    MaintenanceScreen(),
    WaterScreen(),
    ModelsScreenPage(),
    ConfigurationScreen(),
    AboutScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final useRail = width >= 900;

    final body = IndexedStack(index: _index, children: _screens);

    if (useRail) {
      return Scaffold(
        body: Row(
          children: [
            _SideNav(
              index: _index,
              onSelected: (i) => setState(() => _index = i),
              email: ref.watch(authControllerProvider).user?['email'] ?? '—',
              onLogout: () =>
                  ref.read(authControllerProvider.notifier).logout(),
            ),
            const VerticalDivider(width: 1),
            Expanded(child: body),
          ],
        ),
      );
    }

    return Scaffold(
      body: body,
      drawer: _MobileDrawer(
        email: ref.watch(authControllerProvider).user?['email'] ?? '—',
        onLogout: () => ref.read(authControllerProvider.notifier).logout(),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          for (final n in _navItems)
            NavigationDestination(
              icon: Icon(n.icon),
              selectedIcon: Icon(n.iconSelected),
              label: n.label,
            ),
        ],
      ),
    );
  }
}

class _SideNav extends StatelessWidget {
  const _SideNav({
    required this.index,
    required this.onSelected,
    required this.email,
    required this.onLogout,
  });
  final int index;
  final ValueChanged<int> onSelected;
  final String email;
  final VoidCallback onLogout;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: 240,
      color: Theme.of(context).brightness == Brightness.dark
          ? AppColors.oilCharcoal
          : Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [scheme.primary, AppColors.tealAccent],
                    ),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.local_gas_station_rounded,
                      color: Colors.white, size: 20),
                ),
                const SizedBox(width: 10),
                Text(
                  'SmartBarrel',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.3,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 4),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _navItems.length,
              itemBuilder: (_, i) {
                final item = _navItems[i];
                final selected = i == index;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Material(
                    color: selected
                        ? scheme.primaryContainer
                        : Colors.transparent,
                    borderRadius: BorderRadius.circular(AppRadii.md),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(AppRadii.md),
                      onTap: () => onSelected(i),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 12),
                        child: Row(
                          children: [
                            Icon(
                              selected ? item.iconSelected : item.icon,
                              size: 20,
                              color: selected
                                  ? scheme.onPrimaryContainer
                                  : scheme.onSurfaceVariant,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                item.label,
                                style: TextStyle(
                                  fontWeight: selected
                                      ? FontWeight.w700
                                      : FontWeight.w500,
                                  color: selected
                                      ? scheme.onPrimaryContainer
                                      : scheme.onSurface,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 8, 16),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor: scheme.primaryContainer,
                  child: Icon(Icons.person_rounded,
                      size: 18, color: scheme.onPrimaryContainer),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    email,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
                IconButton(
                  tooltip: 'Déconnexion',
                  icon: const Icon(Icons.logout_rounded, size: 20),
                  onPressed: onLogout,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MobileDrawer extends StatelessWidget {
  const _MobileDrawer({required this.email, required this.onLogout});
  final String email;
  final VoidCallback onLogout;

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 24,
                    backgroundColor:
                        Theme.of(context).colorScheme.primaryContainer,
                    child: const Icon(Icons.person_rounded, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'SmartBarrel',
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        Text(
                          email,
                          style: Theme.of(context).textTheme.bodySmall,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout_rounded),
              title: const Text('Déconnexion'),
              onTap: onLogout,
            ),
          ],
        ),
      ),
    );
  }
}
