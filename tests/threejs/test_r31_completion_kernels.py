"""Analytic/invariant tests for the four outstanding R31 kernels."""
import math
import unittest

from r31_completion_kernels import (
    point_segment_distance_2d, impasto_height, height_gradient, impasto_normal,
    oriented_periodic_detail, eroded_height, rk4_step, integrate_rk4,
    greedy_rectangles,
)


class TestR31Impasto(unittest.TestCase):
    def test_segment_distance_projection_and_degenerate_segment(self):
        self.assertAlmostEqual(point_segment_distance_2d((1,2),(0,0),(2,0)),2)
        self.assertAlmostEqual(point_segment_distance_2d((3,0),(0,0),(2,0)),1)
        self.assertAlmostEqual(point_segment_distance_2d((1,2),(0,0),(0,0)),math.sqrt(5))

    def test_compact_stroke_profile_center_and_support(self):
        stroke=(0,0,2,0,1,0.75)
        self.assertAlmostEqual(impasto_height((1,0),[stroke]),0.75)
        self.assertAlmostEqual(impasto_height((1,1),[stroke]),0)
        self.assertAlmostEqual(impasto_height((1,.5),[stroke]),0.75*(.75**2))

    def test_height_gradient_matches_independent_plane_oracle(self):
        h=lambda p: 2.5*p[0]-.75*p[1]+4
        gx,gy=height_gradient(h,(.3,-.7),1e-4)
        self.assertAlmostEqual(gx,2.5,places=8)
        self.assertAlmostEqual(gy,-.75,places=8)

    def test_perturbed_normal_is_unit_and_faces_upward(self):
        n=impasto_normal((3,4),2)
        self.assertAlmostEqual(math.sqrt(sum(v*v for v in n)),1)
        self.assertGreater(n[1],0)

    def test_rejects_invalid_stroke_width(self):
        with self.assertRaises(ValueError): impasto_height((0,0),[(0,0,1,0,0,1)])


class TestR31FlowErosion(unittest.TestCase):
    def test_oriented_detail_is_periodic_along_flow(self):
        p=(.17,-.23); flow=(1,0); f=.5
        a=oriented_periodic_detail(p,flow,f,.8,.2)
        b=oriented_periodic_detail((p[0]+1/f,p[1]),flow,f,.8,.2)
        self.assertAlmostEqual(a,b,places=12)

    def test_zero_slope_has_no_erosion_detail(self):
        self.assertEqual(eroded_height(12,(.2,.7),(1,0),3,0,.4),12)

    def test_detail_is_bounded_by_declared_amplitude(self):
        for i in range(100):
            h=eroded_height(5,(i*.13,i*.07),(1,2),.4,1,.3)
            self.assertLessEqual(abs(h-5),.4+1e-12)

    def test_rejects_zero_flow_and_invalid_anisotropy(self):
        with self.assertRaises(ValueError): oriented_periodic_detail((0,0),(0,0),1)
        with self.assertRaises(ValueError): oriented_periodic_detail((0,0),(1,0),1,1.1)


class TestR31VectorFields(unittest.TestCase):
    @staticmethod
    def oscillator(state,time):
        x,v=state
        return (v,-x)

    def test_rk4_harmonic_oscillator_converges_fourth_order(self):
        exact=(math.cos(1),-math.sin(1))
        coarse=integrate_rk4(self.oscillator,(1,0),0,1,10)
        fine=integrate_rk4(self.oscillator,(1,0),0,1,20)
        ec=math.hypot(coarse[0]-exact[0],coarse[1]-exact[1])
        ef=math.hypot(fine[0]-exact[0],fine[1]-exact[1])
        self.assertGreater(ec/ef,14.0)
        self.assertLess(ec/ef,18.0)

    def test_constant_vector_field_has_closed_form(self):
        out=integrate_rk4(lambda x,t:(2,-3,4),(1,2,3),0,2,7)
        self.assertAlmostEqual(out[0],5); self.assertAlmostEqual(out[1],-4); self.assertAlmostEqual(out[2],11)

    def test_zero_step_and_reverse_time(self):
        self.assertEqual(rk4_step(lambda x,t:x,(1,2),0,0),(1,2))
        out=integrate_rk4(lambda x,t:(1,),(0,),1,0,10)
        self.assertAlmostEqual(out[0],-1)

    def test_rejects_nonfinite_field_output(self):
        with self.assertRaises(ValueError):
            rk4_step(lambda x,t:(float("nan"),),(1,),0,.1)


class TestR31GreedyVoxelMeshing(unittest.TestCase):
    def test_rectangle_partition_preserves_all_keys_and_area(self):
        mask=[[1,1,2],[1,1,2],[None,2,2]]
        rects=greedy_rectangles(mask)
        covered={}
        for x0,y0,x1,y1,key in rects:
            for y in range(y0,y1):
                for x in range(x0,x1):
                    self.assertNotIn((x,y),covered)
                    covered[(x,y)]=key
        expected={(x,y):mask[y][x] for y in range(3) for x in range(3) if mask[y][x] is not None}
        self.assertEqual(covered,expected)
        self.assertEqual(sum((x1-x0)*(y1-y0) for x0,y0,x1,y1,_ in rects),8)

    def test_material_and_face_attributes_prevent_merging(self):
        a=("stone","top",3); b=("stone","top",4); c=("wood","top",3)
        rects=greedy_rectangles([[a,b],[a,c]])
        self.assertEqual(len(rects),3)

    def test_empty_faces_and_invalid_masks(self):
        self.assertEqual(greedy_rectangles([[None,None]]),[])
        with self.assertRaises(ValueError): greedy_rectangles([[1],[1,2]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
