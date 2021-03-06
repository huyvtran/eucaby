'use strict';

angular.module('eucaby', [
    'ionic',
    'eucaby.controllers',
    'eucaby.filters',
    'eucaby.utils',
    'eucaby.api',
    'eucaby.push'
])
.run([
    '$rootScope',
    '$state',
    '$ionicPlatform',
    '$window',
    'EucabyApi',
    'notifications',
    'storageManager',
function($rootScope, $state, $ionicPlatform, $window, EucabyApi, notifications,
         storageManager) {

    EucabyApi.init();

    $ionicPlatform.ready(function() {
        // Device is ready
        if(window.StatusBar) {
            window.StatusBar.styleDefault();
        }
        notifications.init();
    });

    $rootScope.$on('$stateChangeStart', function(event, toState) {
        if (toState.name !== 'app.login' && toState.name !== 'app.logout' &&
            !storageManager.getAccessToken()) {
            $state.go('app.login');
            event.preventDefault();
        }
    });

    $rootScope.$on('OAuthException', function() {
        $state.go('app.login');
    });
}])

.constant('$ionicLoadingConfig', {
    template: '<ion-spinner icon="lines"/>',
    noBackdrop: true,
    duration: 30000    // 30 seconds
})

.config([
    '$stateProvider',
    '$urlRouterProvider',
    '$ionicConfigProvider',
function($stateProvider, $urlRouterProvider, $ionicConfigProvider) {

    $ionicConfigProvider.tabs.position('bottom');

    $stateProvider
    // Abstract states
    .state('app', {
        url: '/app',
        abstract: true,
        templateUrl: 'templates/menu.html'
    })

    .state('app.tab', {
        url: '/tab',
        abstract: true,
        views: {
            'menu-content': {
                templateUrl: 'templates/tabs.html'
            }
        }
    })

    // States with navigation history stack
    .state('app.login', {
        url: '/login',
        views: {
            'menu-content': {
                templateUrl: 'templates/login.html',
                controller: 'LoginCtrl'
            }
        }
    })
    .state('app.profile', {
        url: '/profile',
        views: {
            'menu-content': {
                templateUrl: 'templates/profile.html',
                controller: 'ProfileCtrl'
            }
        }
    })
    .state('app.settings', {
        url: '/settings',
        views: {
            'menu-content': {
                templateUrl: 'templates/settings.html',
                controller: 'SettingsCtrl'
            }
        }
    })
    .state('app.tab.map', {
        url: '/map',
        views: {
            'tab-map': {
                templateUrl: 'templates/map.html',
                controller: 'MapCtrl'
            }
        }
    })
    .state('app.tab.request', {
        cache: false,
        url: '/request/:id',
        views: {
            'tab-detail': {
                templateUrl: 'templates/request-detail.html',
                controller: 'RequestDetailCtrl'
            }
        }
    })
    .state('app.tab.notification', {
        cache: false,
        url: '/notification/:id',
        views: {
            'tab-detail': {
                templateUrl: 'templates/notification-detail.html',
                controller: 'NotificationDetailCtrl'
            }
        }
    })
    .state('app.tab.outgoing', {
        url: '/outgoing',
        views: {
            'tab-outgoing': {
                templateUrl: 'templates/messages.html',
                controller: 'MessagesListCtrl'
            }
        }
    })
    .state('app.tab.incoming', {
        url: '/incoming',
        views: {
            'tab-incoming': {
                templateUrl: 'templates/messages.html',
                controller: 'MessagesListCtrl'
            }
        }
    })
    .state('app.tab.outgoing_notification', {
        url: '/outgoing_notification/:id',
        views: {
            'tab-outgoing': {
                templateUrl: 'templates/notification-detail.html',
                controller: 'NotificationDetailCtrl'
            }
        }
    })
    .state('app.tab.outgoing_request', {
        url: '/outgoing_request/:id',
        views: {
            'tab-outgoing': {
                templateUrl: 'templates/request-detail.html',
                controller: 'RequestDetailCtrl'
            }
        }
    })
    .state('app.tab.incoming_notification', {
        url: '/incoming_notification/:id',
        views: {
            'tab-incoming': {
                templateUrl: 'templates/notification-detail.html',
                controller: 'NotificationDetailCtrl'
            }
        }
    })
    .state('app.tab.incoming_request', {
        url: '/incoming_request/:id',
        views: {
            'tab-incoming': {
                templateUrl: 'templates/request-detail.html',
                controller: 'RequestDetailCtrl'
            }
        }
    });

  $urlRouterProvider.otherwise('/app/tab/map');

}]);
