from . import config, riemann, interp
from .field import Field, IOField, CellField
from .op import  div, absDiv, snGrad, grad, gradCell, snGradCorr
from .solver import Solver
from .interp import central
from .interp import secondOrder as faceInterpolator
from . import BCs
from . import postpro
from . import timestep
from .mesh import Mesh

from adpy.tensor import Kernel, ExternalFunctionOp
from adpy.variable import Variable, Function, Zeros

import numpy as np
#import adFVMcpp

logger = config.Logger(__name__)


class RCF(Solver):
    defaultConfig = Solver.defaultConfig.copy()
    defaultConfig.update({
                             #specific
                             'Cp': 1004.5, 
                             'gamma': 1.4, 
                             'mu': lambda T:  1.4792e-06*T**1.5/(T+116.), 
                             'Pr': 0.7, 
                             'CFL': 1.2,
                             'stepFactor': 1.2,
                             'timeIntegrator': 'SSPRK', 'nStages': 3,
                             # eulerHLLC DOES NOT WORK
                             'riemannSolver': 'eulerRoe',
                             'objectivePLInfo': None,
                             #'boundaryRiemannSolver': 'eulerLaxFriedrichs',
                             'boundaryRiemannSolver': 'eulerRoe',
                             'readConservative': False,
                             'faceReconstructor': 'secondOrder',
                        })

    def __init__(self, case, **userConfig):
        super(RCF, self).__init__(case, **userConfig)

        self.Cv = self.Cp/self.gamma
        self.R = self.Cp - self.Cv
        self.kappa = lambda mu, T: mu*(self.Cp/self.Pr)
        #self.kappa = lambda mu, T: 0.
        self.riemannSolver = getattr(riemann, self.riemannSolver)
        self.boundaryRiemannSolver = getattr(riemann, self.boundaryRiemannSolver)
        self.faceReconstructor = getattr(interp, self.faceReconstructor)

        self.names = ['rho', 'rhoU', 'rhoE']
        self.dimensions = [(1,), (3,), (1,)]

        self.initSource()

        self.Uref = 33.
        self.Tref = 300.
        self.pref = 1e5
        self.tref = 1.
        self.Jref = 1.
        return

    def compileInit(self):
        mesh = self.mesh.symMesh
        self._primitive = Kernel(self.primitive)
        self._conservative = Kernel(self.conservative)
        meshArgs = mesh.getTensor() + mesh.getScalar()
        BCArgs = self.getBoundaryTensor(0)
        rho, rhoU, rhoE = Variable((mesh.nInternalCells, 1)), Variable((mesh.nInternalCells, 3)), Variable((mesh.nInternalCells, 1)),
        U, T, p = Zeros((mesh.nCells, 3)), Zeros((mesh.nCells, 1)), Zeros((mesh.nCells, 1))
        outputs = tuple([x.getReference() for x in [U, T, p]])
        U, T, p = self._primitive(mesh.nInternalCells, outputs)(rho, rhoU, rhoE)
        U, T, p = self.boundaryInit(U, T, p)
        U, T, p = self.boundary(U, T, p)
        U, T, p = self.boundaryEnd(U, T, p)
        rhoN, rhoUN, rhoEN = self._conservative()(U, T, p)
        self.mapBoundary = Function('init', [rho, rhoU, rhoE] + meshArgs + BCArgs, [rhoN, rhoUN, rhoEN])

    def compileSolver(self):
        self._grad = Kernel(self.gradients)
        self._gradCell = Kernel(self.gradientsCell)
        self._coupledGrad = Kernel(self.gradients)
        self._boundaryGrad = Kernel(self.gradients)
        self._flux = Kernel(self.flux)
        self._coupledFlux = Kernel(self.flux)
        self._characteristicFlux = Kernel(self.flux)
        self._boundaryFlux = Kernel(self.boundaryFlux)
        mesh = self.mesh.symMesh
        meshArgs = mesh.getTensor() + mesh.getScalar()
        sourceArgs = [x[0] for x in self.sourceTerms]
        BCArgs = self.getBoundaryTensor(0)
        extraArgs = [x[0] for x in self.extraArgs]
        # init function
        
        #self.t0 = Variable((1,1))
        self.dt = Variable((1,1))
        #self.t = self.t0
        rho, rhoU, rhoE = Variable((mesh.nInternalCells, 1)), Variable((mesh.nInternalCells, 3)), Variable((mesh.nInternalCells, 1)),
        rhoN, rhoUN, rhoEN = timestep.timeStepper(self.equation, [rho, rhoU, rhoE], self)
        args = [rho, rhoU, rhoE, self.dt] + meshArgs + sourceArgs + BCArgs + extraArgs
        outputs = [rhoN, rhoUN, rhoEN, self.dtc, self.obj]
        io_map = {0: 0, 1:1, 2:2}
        #io_map = {}
        self.map = Function('primal', args, outputs, io_map=io_map)
    
        
    def getBoundaryTensor(self, index=0):
        return super(RCF, self).getBoundaryTensor(index) + \
               sum([phi.getTensor(index) for phi in self.gradFields], [])

    # only reads fields
    @config.timeFunction('Time for reading fields')
    def readFields(self, t, suffix=''):
        with IOField.handle(t):
            U = IOField.read('U' + suffix, skipField=False)
            T = IOField.read('T' + suffix, skipField=False)
            p = IOField.read('p' + suffix, skipField=False)
            if self.readConservative:
                rho = IOField.read('rho' + suffix, skipField=False)
                rhoU = IOField.read('rhoU' + suffix, skipField=False)
                rhoE = IOField.read('rhoE' + suffix, skipField=False)
                U.field, T.field, p.field = [phi.field for phi in self.primitive(rho, rhoU, rhoE)]
            if self.dynamicMesh:
                self.mesh.read(IOField._handle)
        fields = [U, T, p]
        # IO Fields, with phi attribute as a CellField
        if self.firstRun:
            self.U, self.T, self.p = fields
            self.fields = fields
            for phi in self.fields:
                phi.completeField()
            self.gradFields = [CellField(phi.name, None, phi.dimensions + (3,)) for phi in self.fields]
        else:
            self.updateFields(fields)
        self.firstRun = False
        return list(self.conservative(*self.fields))

    # reads and updates ghost cells
    def initFields(self, fields):
        mesh = self.mesh
        newFields = self.mapBoundary(*[phi.field for phi in fields] + mesh.getTensor() + mesh.getScalar() + self.getBoundaryTensor(1))
        return self.getFields(newFields, IOField, refFields=fields)
    
    @config.timeFunction('Time for writing fields')
    def writeFields(self, fields, t):
        n = len(self.names)
        fields, rest = fields[:n], fields[n:]
        fields = self.initFields(fields)
        U, T, p = self.primitive(*fields)
        for phi, phiN in zip(self.fields, [U, T, p]):
            phi.field = phiN.field

        with IOField.handle(t):
            for phi in fields + self.fields + rest:
                phi.write(skipProcessor=True)
            if self.dynamicMesh:
                self.mesh.write(IOField._handle)
        return

    # operations, dual
    def primitive(self, rho, rhoU, rhoE):
        logger.info('converting fields to primitive')
        U = rhoU/rho
        E = rhoE/rho
        e = E - 0.5*U.magSqr()
        p = (self.gamma-1)*rho*e
        T = e*(1./self.Cv)
        if isinstance(U, Field):
            U.name, T.name, p.name = 'U', 'T', 'p'
        return U, T, p

    def conservative(self, U, T, p):
        logger.info('converting fields to conservative')
        e = self.Cv*T
        rho = p/(e*(self.gamma-1))
        rhoE = rho*(e + 0.5*U.magSqr())
        rhoU = U*rho
        if isinstance(U, Field):
            rho.name, rhoU.name, rhoE.name = self.names
        return rho, rhoU, rhoE

    # used in symbolic
    def getFlux(self, U, T, p, Normals):
        rho, rhoU, rhoE = self.conservative(U, T, p)
        Un = U.dot(Normals)
        rhoFlux = rho*Un
        rhoUFlux = rhoU*Un + p*Normals
        rhoEFlux = (rhoE + p)*Un
        return rhoFlux, rhoUFlux, rhoEFlux

    def viscousFlux(self, TL, TR, UL, UR, TF, UF, gradTF, gradUF, mesh):
        mu = self.mu(TF)
        kappa = self.kappa(mu, TF)
        D = mesh.deltasUnit
        N = mesh.normals

        # charles
        gradTF = gradTF[0] + snGrad(TL, TR, mesh)*D - gradTF[0].dot(D)*D
        gradUF =  gradUF + snGrad(UL, UR, mesh).outer(D) - gradUF.tensordot(D).outer(D)
        # stable, too dissipative
        #gradTF = gradTF[0]
        #gradUF = gradUF 
        qF = kappa*gradTF.dot(N)
        tmp2 = (gradUF + gradUF.transpose()).tensordot(N)

        # no snGrad correction
        #qF = kappa*snGrad(TL, TR, mesh)
        #tmp2 = snGrad(UL, UR, mesh) + gradUF.transpose().tensordot(N)
        # snGrad correction 
        #qF = kappa*snGradCorr(TL, TR, gradTF, mesh)
        #tmp2 = snGradCorr(UL, UR, gradUF, mesh) + gradUF.transpose().tensordot(N)
        # old theano setup
        #qF = kappa*snGrad(TL, TR, mesh)
        #tmp2 = (gradUF + gradUF.transpose()).tensordot(N)

        tmp3 = gradUF.trace()
        sigmaF = mu*(tmp2-2./3*tmp3*N)

        rhoUFlux = -sigmaF
        rhoEFlux = -(qF + sigmaF.dot(UF))
        return rhoUFlux, rhoEFlux

    #symbolic funcs
    def gradients(self, U, T, p, *mesh, **options):
        mesh = Mesh.container(mesh)
        neighbour = options.pop('neighbour', True)
        boundary = options.pop('boundary', False)
        if boundary:
            UF = U.extract(mesh.neighbour)
            TF = T.extract(mesh.neighbour)
            pF = p.extract(mesh.neighbour)
        else:
            UF = central(U, mesh)
            TF = central(T, mesh)
            pF = central(p, mesh)

        gradU = grad(UF, mesh, neighbour)
        gradT = grad(TF, mesh, neighbour)
        gradp = grad(pF, mesh, neighbour)

        return gradU, gradT, gradp


    def gradientsCell(self, U, T, p, *mesh):
        mesh = Mesh.container(mesh)
        gradU = gradCell(U, mesh)
        gradT = gradCell(T, mesh)
        gradp = gradCell(p, mesh)
        
        return gradU, gradT, gradp
        
    def flux(self, U, T, p, gradU, gradT, gradp, *mesh, **options):
        mesh = Mesh.container(mesh)
        neighbour = options.pop('neighbour', True)
        characteristic = options.pop('characteristic', False)
        P, N = mesh.owner, mesh.neighbour

        ULF = faceInterpolator(U, gradU, mesh, 0)
        TLF = faceInterpolator(T, gradT, mesh, 0)
        pLF = faceInterpolator(p, gradp, mesh, 0)
        rhoLF, rhoULF, rhoELF = self.conservative(ULF, TLF, pLF)
        TL, TR = T.extract(P), T.extract(N)
        UL, UR = U.extract(P), U.extract(N)

        if characteristic:
            URF, TRF, pRF = UR, TR, p.extract(N)
            rhoRF, rhoURF, rhoERF = self.conservative(URF, TRF, pRF)
            rhoFlux, rhoUFlux, rhoEFlux = self.boundaryRiemannSolver(self.gamma, pLF, pRF, TLF, TRF, ULF, URF, \
            rhoLF, rhoRF, rhoULF, rhoURF, rhoELF, rhoERF, mesh.normals)
            TF = TR
            UF = UR
            gradTF = gradT.extract(N)
            gradUF = gradU.extract(N)
        else:
            URF = faceInterpolator(U, gradU, mesh, 1)
            TRF = faceInterpolator(T, gradT,  mesh, 1)
            pRF = faceInterpolator(p, gradp, mesh, 1)
            rhoRF, rhoURF, rhoERF = self.conservative(URF, TRF, pRF)
            rhoFlux, rhoUFlux, rhoEFlux = self.riemannSolver(self.gamma, pLF, pRF, TLF, TRF, ULF, URF, \
            rhoLF, rhoRF, rhoULF, rhoURF, rhoELF, rhoERF, mesh.normals)
            # more accurate
            UF = 0.5*(ULF + URF)
            TF = 0.5*(TLF + TRF)
            #gradUF = central(gradU, mesh)
            #gradTF = central(gradT, mesh)
            # charles
            #TF = 0.5*(TL + TR)
            #UF = 0.5*(UL + UR)
            gradTF = 0.5*(gradT.extract(P) + gradT.extract(N))
            gradUF = 0.5*(gradU.extract(P) + gradU.extract(N))

        ret = self.viscousFlux(TL, TR, UL, UR, TF, UF, gradTF, gradUF, mesh)
        rhoUFlux += ret[0]
        rhoEFlux += ret[1]

        drho = div(rhoFlux, mesh, neighbour)
        drhoU = div(rhoUFlux, mesh, neighbour)
        drhoE = div(rhoEFlux, mesh, neighbour)

        aF = (self.Cp*TF*(self.gamma-1)).sqrt()
        maxaF = abs(UF.dot(mesh.normals)) + aF
        dtc = absDiv(maxaF, mesh, neighbour)

        return drho, drhoU, drhoE, dtc

    def boundaryFlux(self, U, T, p, gradU, gradT, gradp, *mesh):
        mesh = Mesh.container(mesh)
        P, N = mesh.owner, mesh.neighbour

        # boundary extraction could be done using cellstartface
        UR, TR, pR = U.extract(N), T.extract(N), p.extract(N) 
        #UR, TR, pR = U, T, p
        gradUR, gradTR = gradU.extract(N), gradT.extract(N)
        TL = T.extract(P)
        UL = U.extract(P)

        rhoFlux, rhoUFlux, rhoEFlux = self.getFlux(UR, TR, pR, mesh.normals)
        ret = self.viscousFlux(TL, TR, UL, UR, TR, UR, gradTR, gradUR, mesh)
        rhoUFlux += ret[0]
        rhoEFlux += ret[1]

        drho = div(rhoFlux, mesh, False)
        drhoU = div(rhoUFlux, mesh, False)
        drhoE = div(rhoEFlux, mesh, False)

        aF = (self.Cp*TR*(self.gamma-1)).sqrt()
        maxaF = abs(UR.dot(mesh.normals)) + aF
        dtc = absDiv(maxaF, mesh, False)

        return drho, drhoU, drhoE, dtc

    def characteristicBoundary(self, U, T, p):
        for patchID, patch in self.p.phi.BC.items():
            if isinstance(patch, BCs.CharacteristicBoundaryCondition):
                U, T, p = patch.update(U, T, p)
        return U, T, p

    def equation(self, rho, rhoU, rhoE):
        logger.info('computing RHS/LHS')
        mesh = self.mesh.symMesh

        def _meshArgs(start=0):
            return [x[start] for x in mesh.getTensor()]

        U, T, p = Zeros((mesh.nCells, 3)), Zeros((mesh.nCells, 1)), Zeros((mesh.nCells, 1))
        outputs = self._primitive(mesh.nInternalCells, (U, T, p))(rho, rhoU, rhoE)
        # boundary update
        outputs = self.boundaryInit(*outputs)
        #is this right?
        outputs = self.boundary(*outputs)
        outputs = self.boundaryEnd(*outputs)
        U, T, p = outputs
        if self.objective is not None:
            obj = self.objective([U, T, p], self)
        else:
            obj = Zeros((1,1))

        meshArgs = _meshArgs()
        gradU, gradT, gradp = Zeros((mesh.nCells, 3, 3)), Zeros((mesh.nCells, 1, 3)), Zeros((mesh.nCells, 1, 3))

        #outputs = self._grad(mesh.nInternalFaces, (gradU, gradT, gradp))(U, T, p, *meshArgs)
        #for patchID in self.mesh.sortedPatches:
        #    startFace, nFaces = mesh.boundary[patchID]['startFace'], mesh.boundary[patchID]['nFaces']
        #    patchType = self.mesh.boundary[patchID]['type']
        #    meshArgs = _meshArgs(startFace)
        #    if patchType in config.coupledPatches:
        #        outputs = self._coupledGrad(nFaces, outputs)(U, T, p, neighbour=False, boundary=False, *meshArgs)
        #        outputs[0].args[0].info += [[x.shape for x in self.mesh.getTensor()], patchID, self.mesh.boundary[patchID]['startFace'], self.mesh.boundary[patchID]['nFaces']]
        #    else:
        #        outputs = self._boundaryGrad(nFaces, outputs)(U, T, p, neighbour=False, boundary=True, *meshArgs)
        #meshArgs = _meshArgs(mesh.nLocalFaces)
        #outputs = self._coupledGrad(mesh.nRemoteCells, outputs)(U, T, p, neighbour=False, boundary=False, *meshArgs)
        outputs = self._gradCell(mesh.nInternalCells, (gradU, gradT, gradp))(U, T, p, *meshArgs)

        # grad boundary update
        outputs = list(self.boundaryInit(*outputs))
        for index, phi in enumerate(outputs):
            phi = self.gradFields[index].updateGhostCells(phi)
            #if not config.gpu:
            #    phi = ExternalFunctionOp('mpi', (phi,), (phi,)).outputs[0]
            phi = ExternalFunctionOp('mpi', (phi,), (phi,)).outputs[0]
            outputs[index] = phi
        outputs = self.boundaryEnd(*outputs)
        gradU, gradT, gradp = outputs
        
        meshArgs = _meshArgs()
        drho, drhoU, drhoE = Zeros((mesh.nInternalCells, 1)), Zeros((mesh.nInternalCells, 3)), Zeros((mesh.nInternalCells, 1))
        dtc = Zeros((mesh.nInternalCells, 1))
        outputs = self._flux(mesh.nInternalFaces, (drho, drhoU, drhoE, dtc))(U, T, p, gradU, gradT, gradp, *meshArgs)
        for patchID in self.mesh.sortedPatches:
            startFace, nFaces = mesh.boundary[patchID]['startFace'], mesh.boundary[patchID]['nFaces']
            patchType = self.mesh.boundary[patchID]['type']
            meshArgs = _meshArgs(startFace)
            if patchType in config.coupledPatches:
                outputs = self._coupledFlux(nFaces, outputs)(U, T, p, gradU, gradT, gradp, characteristic=False, neighbour=False, *meshArgs)
            elif patchType == 'characteristic':
                outputs = self._characteristicFlux(nFaces, outputs)(U, T, p, gradU, gradT, gradp, characteristic=True, neighbour=False, *meshArgs)
            else:
                outputs = self._boundaryFlux(nFaces, outputs)(U, T, p, gradU, gradT, gradp, *meshArgs)
        meshArgs = _meshArgs(mesh.nLocalFaces)
        outputs = self._coupledFlux(mesh.nRemoteCells, outputs)(U, T, p, gradU, gradT, gradp, characteristic=False, neighbour=False, *meshArgs)
        drho, drhoU, drhoE, dtc = outputs

        def _minDtc(dtc):
            #dtc = (dtc**-1)*(2*self.CFL)
            #return dtc.reduce_min()
            return dtc.reduce_max()
        minDtc = Zeros((1, 1))
        minDtc = Kernel(_minDtc)(mesh.nInternalCells, (minDtc,))(dtc)

        if self.stage == 1:
            self.dtc, self.obj = minDtc, obj
        return drho, drhoU, drhoE

    def boundary(self, U, T, p):
        outputs = super(RCF, self).boundary(U, T, p, boundary=[phi.phi for phi in self.fields])
        return self.characteristicBoundary(*outputs)
