import { onBeforeUnmount, onMounted } from "vue";
import { animate, inView, stagger } from "motion";

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function useMotionReveal(rootRef, options = {}) {
  const {
    initialSelector = "[data-reveal]",
    scrollSelector = "[data-reveal-scroll]"
  } = options;
  const stops = [];

  onMounted(() => {
    const root = rootRef?.value || document;
    const initialTargets = Array.from(root.querySelectorAll(initialSelector));
    const scrollTargets = Array.from(root.querySelectorAll(scrollSelector));

    if (prefersReducedMotion()) {
      [...initialTargets, ...scrollTargets].forEach((element) => {
        element.style.opacity = 1;
        element.style.transform = "none";
        element.style.filter = "none";
      });
      return;
    }

    if (initialTargets.length) {
      initialTargets.forEach((element) => {
        element.style.opacity = "0";
        element.style.transform = "translateY(20px)";
        element.style.filter = "blur(10px)";
      });
      animate(
        initialTargets,
        { opacity: [0, 1], y: [20, 0], filter: ["blur(10px)", "blur(0px)"] },
        {
          delay: stagger(0.06),
          duration: 0.68,
          easing: [0.22, 1, 0.36, 1]
        }
      ).then(() => {
        initialTargets.forEach((element) => {
          element.style.opacity = "";
          element.style.transform = "";
          element.style.filter = "";
        });
      });
    }

    scrollTargets.forEach((element, index) => {
      element.style.opacity = "0";
      element.style.transform = "translateY(28px)";
      element.style.filter = "blur(8px)";
      const stop = inView(
        element,
        () =>
          animate(
            element,
            { opacity: [0, 1], y: [28, 0], filter: ["blur(8px)", "blur(0px)"] },
            {
              delay: index * 0.02,
              duration: 0.7,
              easing: [0.22, 1, 0.36, 1]
            }
          ).then(() => {
            element.style.opacity = "";
            element.style.transform = "";
            element.style.filter = "";
          }),
        { margin: "0px 0px -60px 0px" }
      );
      stops.push(stop);
    });
  });

  onBeforeUnmount(() => {
    stops.forEach((stop) => stop?.());
  });
}
