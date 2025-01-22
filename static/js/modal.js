
    /**
    * Modal
    * modal.openModal('modal-name');
    */

    const modal = (() => {

      var publicAPIs = { };


    //
    // Settings
    //
    var settings = {
        speedOpen: 50,
    speedClose: 250,
    toggleClass: 'hidden',
    selectorTarget: '[data-modal-target]',
    selectorTrigger: '[data-modal-trigger]',
    selectorClose: '[data-modal-close]',
    selectorOverlay: '[data-modal-overlay]',
    selectorWrapper: '[data-modal-wrapper]',
    selectorInputFocus: '[data-modal-input-focus]'
      };


    /**
    * Element.closest() polyfill
    * https://developer.mozilla.org/en-US/docs/Web/API/Element/closest#Polyfill
    */
    if (!Element.prototype.closest) {
        if (!Element.prototype.matches) {
        Element.prototype.matches = Element.prototype.msMatchesSelector || Element.prototype.webkitMatchesSelector;
        }
    Element.prototype.closest = function (s) {
          var el = this;
    var ancestor = this;
    if (!document.documentElement.contains(el)) return null;
    do {
            if (ancestor.matches(s)) return ancestor;
    ancestor = ancestor.parentElement;
          } while (ancestor !== null);
    return null;
        };
      }

    // Trap Focus
    // https://hiddedevries.nl/en/blog/2017-01-29-using-javascript-to-trap-focus-in-an-element
    //
    function trapFocus(element) {
        var focusableEls = element.querySelectorAll('a[href]:not([disabled]), button:not([disabled]), textarea:not([disabled]), input[type="text"]:not([disabled]), input[type="radio"]:not([disabled]), input[type="checkbox"]:not([disabled]), select:not([disabled])');
    var firstFocusableEl = focusableEls[0];
    var lastFocusableEl = focusableEls[focusableEls.length - 1];
    var KEYCODE_TAB = 9;

    element.addEventListener('keydown', function(e) {
          var isTabPressed = (e.key === 'Tab' || e.keyCode === KEYCODE_TAB);

    if (!isTabPressed) {
            return;
          }

    if ( e.shiftKey ) /* shift + tab */ {
            if (document.activeElement === firstFocusableEl) {
        lastFocusableEl.focus();
    e.preventDefault();
              }
            } else /* tab */ {
            if (document.activeElement === lastFocusableEl) {
        firstFocusableEl.focus();
    e.preventDefault();
              }
            }
        });
      }


    //
    // Methods
    //

    // Toggle accessibility
    var toggleccessibility = function (event) {
        if (event.getAttribute('aria-expanded') === 'true') {
        event.setAttribute('aria-expanded', false);
        } else {
        event.setAttribute('aria-expanded', true);
        }
      };

    // Open Modal
    var openModal = function (event, destination) {

        var target = destination;

    // Check whether the modal is triggered automatically via modal.openModal
    if (typeof event === 'string') {
        target = document.getElementById(event);
    // If modal is triggered via modal.openModal we add a data attribute
    // to know whether toggleccessibility() should be used when closeModal
    // as there is no button used
    if (target) {
        target.setAttribute('data-auto-trigger', '');
          }
        }

    // If target doesn't exist, bail
    if (!target) return;

    // Find target
    var overlay = target.querySelector(settings.selectorOverlay),
    wrapper = target.querySelector(settings.selectorWrapper),
    input = target.querySelector(settings.selectorInputFocus);

    // Make it active and remoe hidden class
    target.classList.remove(settings.toggleClass);

    // Make body overflow hidden so it's not scrollable
    document.documentElement.style.overflow = 'hidden';

    // Toggle accessibility
    // Check whether the modal is triggered automatically via modal.openModal
    if (typeof event !== 'string') {
        toggleccessibility(event);
        }

    // Show wrapper
    setTimeout(function () {

          // Show overlay
          if (overlay) {
            var overlayIn = overlay.getAttribute('data-class-in').split(' '),
    overlayOut = overlay.getAttribute('data-class-out').split(' ');
    overlay.classList.remove(...overlayOut);
    overlay.classList.add(...overlayIn);
          }

    // Show drawer
    if (wrapper) {
            var wrapperIn = wrapper.getAttribute('data-class-in').split(' '),
    wrapperOut = wrapper.getAttribute('data-class-out').split(' ');
    wrapper.classList.remove(...wrapperOut);
    wrapper.classList.add(...wrapperIn);
          }

    // Focus on input
    if (input) {
        input.focus();
          }

    // Trap focus
    trapFocus(target);

        }, settings.speedOpen);

      };

    // Close Modal
    var closeModal = function (event) {

        // Find target
        var closestParent = event.closest(settings.selectorTarget),
    trigger = document.querySelector('[aria-controls="' + closestParent.id + '"'),
    overlay = closestParent.querySelector(settings.selectorOverlay),
    wrapper = closestParent.querySelector(settings.selectorWrapper);

    if (trigger === null) {
        trigger = document.querySelector('a[href="#' + closestParent.id + '"');
        }

    // Hide overlay
    if (overlay) {
          var overlayIn = overlay.getAttribute('data-class-in').split(' '),
    overlayOut = overlay.getAttribute('data-class-out').split(' ');
    overlay.classList.remove(...overlayIn);
    overlay.classList.add(...overlayOut);
        }

    // Hide wrapper
    if (wrapper) {
          var wrapperIn = wrapper.getAttribute('data-class-in').split(' '),
    wrapperOut = wrapper.getAttribute('data-class-out').split(' ');
    wrapper.classList.remove(...wrapperIn);
    wrapper.classList.add(...wrapperOut);
        }

    // Remove body overflow hidden
    document.documentElement.style.overflow = '';

    // Toggle accessibility
    // Check whether the modal was triggered automatically via modal.openModal
    if (closestParent.hasAttribute('data-auto-trigger')) {
        closestParent.removeAttribute('data-auto-trigger');
        } else {
        toggleccessibility(trigger);
        }

    // Make it not active
    setTimeout(function () {
        closestParent.classList.add(settings.toggleClass);
        }, settings.speedClose);

      };

    // Click Handler
    var clickHandler = function (event) {

        // Find toggle element
        var toggle = event.target,
    trigger,
    target,
    closestButton = toggle.closest('button'),
    closest = toggle.closest('a'),
    open = null;

        // Check whether toggle is:
        // 1. <button data-modal-trigger aria-controls="modal-name" ...
        // 2. <button data-modal-trigger aria-controls="modal-name"><span>...</span> ...
        // 3. <a href="#modal-name" ...
        // 4. <a href="#modal-name"><span>...</span> ...
            // 5. null
            if ( toggle.hasAttribute('data-modal-trigger') && (toggle.hasAttribute('aria-controls')) ) {
                trigger = toggle.closest(settings.selectorTrigger);
            target = document.getElementById(trigger.getAttribute('aria-controls'));
            open = true;
        } else if ( closestButton && closestButton.hasAttribute('data-modal-trigger') && (closestButton.hasAttribute('aria-controls')) ) {
                trigger = toggle.closest(settings.selectorTrigger);
            target = document.getElementById(trigger.getAttribute('aria-controls'));
            open = true;
        } else if ( (toggle.hash) && (toggle.hash.substr(1).indexOf('modal') > -1) ) {
                trigger = toggle;
            target = document.getElementById(toggle.hash.substr(1));
            open = true;
        }  else if ( closest && (closest.hash) && (closest.hash.substr(1).indexOf('modal') > -1) ) {
                trigger = closest;
            target = document.getElementById(closest.hash.substr(1));
            open = true;
        }

            var close = toggle.closest(settings.selectorClose);

            // Open modal when the open button is clicked
            if (open && target) {
                openModal(trigger, target);
        }

            // Close modal when the close button (or overlay area) is clicked
            if (close) {
                closeModal(close);
        }

            // Prevent default link behavior
            if (open || close) {
                event.preventDefault();
        }

      };

            // Keydown Handler, handle Escape button
            var keydownHandler = function (event) {

        if (event.key === 'Escape' || event.keyCode === 27) {

          // Find all possible modals
          var modals = document.querySelectorAll(settings.selectorTarget),
            i;

            // Find active modals and close them when escape is clicked
            for (i = 0; i < modals.length; ++i) {
            if (!modals[i].classList.contains(settings.toggleClass)) {
                closeModal(modals[i]);
            }
          }

        }

      };


            publicAPIs.init = function () {
                //
                // Inits & Event Listeners
                //
                document.addEventListener('click', clickHandler, false);
            document.addEventListener('keydown', keydownHandler, false);
      };

            publicAPIs.openModal = openModal;
            publicAPIs.closeModal = closeModal;

            return publicAPIs;

    })();

            document.addEventListener("DOMContentLoaded", function() {
                modal.init()
            });